import requests
import json
import hashlib
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from dynamics_search.models import Part


class Command(BaseCommand):
    help = 'Sync parts from Dynamics 365 OData endpoint'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            default=getattr(settings, 'DYNAMICS_COMPANY', 'yourcompany'),
            help='Dynamics 365 company name (default: yourcompany)'
        )
        parser.add_argument(
            '--client-id',
            type=str,
            default=getattr(settings, 'DYNAMICS_CLIENT_ID', ''),
            help='Azure AD Client ID for OAuth'
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            default=getattr(settings, 'DYNAMICS_CLIENT_SECRET', ''),
            help='Azure AD Client Secret for OAuth'
        )
        parser.add_argument(
            '--tenant-id',
            type=str,
            default=getattr(settings, 'DYNAMICS_TENANT_ID', ''),
            help='Azure AD Tenant ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes'
        )
    
    def handle(self, *args, **options):
        company = options['company']
        client_id = options['client_id']
        client_secret = options['client_secret']
        tenant_id = options['tenant_id']
        dry_run = options['dry_run']
        
        if not all([client_id, client_secret, tenant_id]):
            raise CommandError(
                'Missing OAuth credentials. Set DYNAMICS_CLIENT_ID, '
                'DYNAMICS_CLIENT_SECRET, and DYNAMICS_TENANT_ID in settings '
                'or use command line arguments.'
            )
        
        self.stdout.write(f"Starting parts sync for {company}...")
        
        try:
            # Get OAuth token
            token = self.get_oauth_token(client_id, client_secret, tenant_id)
            
            # Fetch parts from Dynamics 365
            parts_data = self.fetch_parts(company, token)
            
            if dry_run:
                self.stdout.write(f"DRY RUN: Would sync {len(parts_data)} parts")
                for part in parts_data[:5]:  # Show first 5
                    self.stdout.write(f"  - {part.get('item_number', 'N/A')}: {part.get('description', 'N/A')[:50]}")
                if len(parts_data) > 5:
                    self.stdout.write(f"  ... and {len(parts_data) - 5} more")
                return
            
            # Sync parts to database
            created_count, updated_count = self.sync_parts(parts_data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sync completed: {created_count} created, {updated_count} updated"
                )
            )
            
        except Exception as e:
            raise CommandError(f"Sync failed: {str(e)}")
    
    def get_oauth_token(self, client_id, client_secret, tenant_id):
        """Get OAuth 2.0 access token from Azure AD"""
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data['access_token']
    
    def fetch_parts(self, company, token):
        """Fetch all parts from Dynamics 365 OData endpoint"""
        base_url = f"https://{company}.crm.dynamics.com/api/data/v9.2/parts"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0'
        }
        
        all_parts = []
        next_url = base_url
        
        while next_url:
            self.stdout.write(f"Fetching: {next_url}")
            
            response = requests.get(next_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            parts = data.get('value', [])
            all_parts.extend(parts)
            
            # Check for next page
            next_url = data.get('@odata.nextLink')
            
            self.stdout.write(f"  Fetched {len(parts)} parts (total: {len(all_parts)})")
        
        return all_parts
    
    def sync_parts(self, parts_data):
        """Sync parts data to database using bulk operations"""
        created_count = 0
        updated_count = 0
        
        # Get existing parts for comparison
        existing_parts = {
            part.item_number: part 
            for part in Part.objects.all()
        }
        
        parts_to_create = []
        parts_to_update = []
        
        for part_data in parts_data:
            item_number = part_data.get('item_number', '').strip()
            if not item_number:
                continue
            
            description = part_data.get('description', '').strip()
            size = part_data.get('size', '').strip()
            
            # Generate content hash for change detection
            content_hash = hashlib.md5(f"{description}|{size}".encode()).hexdigest()
            
            if item_number in existing_parts:
                existing_part = existing_parts[item_number]
                
                # Check if content has changed
                if existing_part.content_hash != content_hash:
                    existing_part.description = description
                    existing_part.size = size
                    parts_to_update.append(existing_part)
            else:
                # New part
                new_part = Part(
                    item_number=item_number,
                    description=description,
                    size=size
                )
                parts_to_create.append(new_part)
        
        # Bulk operations
        with transaction.atomic():
            if parts_to_create:
                Part.objects.bulk_create(parts_to_create, batch_size=1000)
                created_count = len(parts_to_create)
                self.stdout.write(f"Created {created_count} new parts")
            
            if parts_to_update:
                Part.objects.bulk_update(
                    parts_to_update, 
                    ['description', 'size', 'last_updated'],
                    batch_size=1000
                )
                updated_count = len(parts_to_update)
                self.stdout.write(f"Updated {updated_count} existing parts")
        
        return created_count, updated_count
