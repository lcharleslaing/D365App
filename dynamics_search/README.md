# Dynamics Search App

A Django app for searching and managing parts from Dynamics 365 with advanced search capabilities.

## Features

- **Full-text Search**: PostgreSQL-powered search with trigram similarity
- **Wildcard Support**: Use `%` wildcards for flexible searching (e.g., `%hose%`)
- **Live Search**: HTMX-powered instant search results as you type
- **Modern UI**: Clean, responsive interface using TailwindCSS/DaisyUI
- **Dynamics 365 Integration**: Sync parts from Dynamics 365 OData endpoint
- **Bulk Operations**: Efficient bulk create/update for large datasets
- **Export Functionality**: Export search results to CSV

## Models

### Part
- `id`: Auto-incrementing primary key
- `item_number`: Unique part identifier (max 50 chars)
- `description`: Full part description (text field)
- `size`: Part size specification (max 20 chars, optional)
- `last_updated`: Automatic timestamp of last update
- `search_vector`: Full-text search vector (auto-generated)

## Management Commands

### `run_parts_sync`
Syncs parts from Dynamics 365 OData endpoint.

```bash
# Basic sync
python manage.py run_parts_sync

# With custom company
python manage.py run_parts_sync --company yourcompany

# With OAuth credentials
python manage.py run_parts_sync --client-id YOUR_CLIENT_ID --client-secret YOUR_SECRET --tenant-id YOUR_TENANT_ID

# Dry run (show what would be synced)
python manage.py run_parts_sync --dry-run
```

### `seed_parts`
Creates sample parts data for testing.

```bash
# Create 100 sample parts
python manage.py seed_parts

# Create custom amount
python manage.py seed_parts --count 50

# Clear existing and create new
python manage.py seed_parts --clear --count 200
```

## API Endpoints

- `GET /search/` - Main search page
- `GET /search/api/` - Search API endpoint
- `GET /search/suggestions/` - Autocomplete suggestions
- `GET /search/part/<id>/` - Part detail page

## Search Features

### Basic Search
- Search by item number, description, or size
- Case-insensitive matching
- Multiple terms supported

### Wildcard Search
- Use `%` for wildcards: `%hose%` finds all parts containing "hose"
- Multiple wildcards: `%valve%steel%` finds parts with both "valve" and "steel"

### Trigram Similarity
- Fuzzy matching for typos and similar terms
- Results ranked by similarity score
- Configurable similarity threshold

## Configuration

### Settings
Add to your `settings.py`:

```python
# Dynamics 365 Configuration
DYNAMICS_COMPANY = 'yourcompany'
DYNAMICS_CLIENT_ID = 'your-client-id'
DYNAMICS_CLIENT_SECRET = 'your-client-secret'
DYNAMICS_TENANT_ID = 'your-tenant-id'

# Search Configuration
SEARCH_RESULTS_PER_PAGE = 20
SEARCH_MIN_QUERY_LENGTH = 2
```

### Database
For full-text search features, use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Dependencies

- `requests` - For Dynamics 365 API calls
- `pandas` - For data processing (optional)
- `django.contrib.postgres` - For full-text search (PostgreSQL only)

## Usage Examples

### Search API
```javascript
// Basic search
fetch('/search/api/?q=valve')

// Wildcard search
fetch('/search/api/?q=%hose%steel%')

// Paginated results
fetch('/search/api/?q=pipe&page=2&per_page=10')
```

### Management Command
```python
from django.core.management import call_command

# Sync parts programmatically
call_command('run_parts_sync', company='yourcompany')
```

## Admin Interface

The app includes a custom admin interface with:
- Search and filtering capabilities
- Bulk actions for refreshing search vectors
- Read-only system fields
- Optimized querysets

## Templates

- `search.html` - Main search interface with HTMX
- `part_detail.html` - Individual part detail page
- Extends the global `home.html` template

## Styling

Uses TailwindCSS and DaisyUI for:
- Responsive design
- Modern card-based layout
- Interactive components
- Consistent styling with the main application
