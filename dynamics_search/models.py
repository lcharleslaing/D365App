from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.conf import settings

# Import PostgreSQL features only if using PostgreSQL
try:
    from django.contrib.postgres.indexes import GinIndex
    from django.contrib.postgres.search import SearchVectorField
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class Part(models.Model):
    id = models.AutoField(primary_key=True)
    item_number = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    size = models.CharField(max_length=20, blank=True)
    product_group_id = models.CharField(max_length=50, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit_cost_date = models.DateTimeField(null=True, blank=True)
    vendor_name = models.CharField(max_length=255, blank=True)
    vendor_product_number = models.CharField(max_length=100, blank=True)
    vendor_product_description = models.TextField(blank=True)
    vendor_phone = models.CharField(max_length=20, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Full-text search vector field (PostgreSQL only)
    search_vector = models.TextField(null=True, blank=True) if not POSTGRES_AVAILABLE else SearchVectorField(null=True, blank=True)
    
    class Meta:
        ordering = ['item_number']
        indexes = [
            # Regular indexes for common lookups
            models.Index(fields=['item_number']),
            models.Index(fields=['last_updated']),
        ]
        
        # Add PostgreSQL-specific indexes if available
        if POSTGRES_AVAILABLE and 'postgresql' in settings.DATABASES['default']['ENGINE']:
            indexes.append(GinIndex(fields=['search_vector']))
    
    def __str__(self):
        return f"{self.item_number} - {self.description[:50] if self.description else 'No Description'}"
    
    def save(self, *args, **kwargs):
        # Update search vector when saving
        search_parts = []
        if self.item_number:
            search_parts.append(str(self.item_number))
        if self.description:
            search_parts.append(str(self.description))
        if self.size:
            search_parts.append(str(self.size))
        if self.product_group_id:
            search_parts.append(str(self.product_group_id))
        if self.vendor_name:
            search_parts.append(str(self.vendor_name))
        if self.vendor_product_number:
            search_parts.append(str(self.vendor_product_number))
        if self.vendor_product_description:
            search_parts.append(str(self.vendor_product_description))
        
        self.search_vector = ' '.join(search_parts)
        super().save(*args, **kwargs)
    
    @property
    def content_hash(self):
        """Generate hash for change detection"""
        import hashlib
        content = f"{self.description}|{self.size}|{self.product_group_id}|{self.unit_cost}|{self.vendor_name}|{self.vendor_product_number}|{self.vendor_product_description}"
        return hashlib.md5(content.encode()).hexdigest()