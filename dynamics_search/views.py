from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import re

from .models import Part

# Import PostgreSQL features only if using PostgreSQL
try:
    from django.contrib.postgres.search import TrigramSimilarity, SearchQuery, SearchRank
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


def search_page(request):
    """Main search page with HTMX-powered live search"""
    return render(request, 'dynamics_search/search.html')


@require_http_methods(["GET"])
def search_api(request):
    """API endpoint for part search with trigram and wildcard support"""
    query = request.GET.get('q', '').strip()
    columns = request.GET.getlist('columns')  # Get list of selected columns
    
    
    if not query:
        return JsonResponse({
            'results': [],
            'total': 0,
            'query': query
        })
    
    # Parse wildcards and build search conditions based on selected columns
    search_conditions = build_search_conditions(query, columns)
    
    # Base queryset
    queryset = Part.objects.all()
    
    # Apply search conditions
    if search_conditions:
        queryset = queryset.filter(search_conditions)
    
    # Add similarity ranking (PostgreSQL trigram or basic SQLite)
    # Only calculate similarity for the columns that were actually searched
    if POSTGRES_AVAILABLE and 'postgresql' in settings.DATABASES['default']['ENGINE']:
        # Use PostgreSQL trigram similarity based on selected columns
        similarity_conditions = []
        if not columns or 'item_number' in columns:
            similarity_conditions.append(TrigramSimilarity('item_number', query))
        if not columns or 'description' in columns:
            similarity_conditions.append(TrigramSimilarity('description', query))
        if not columns or 'size' in columns:
            similarity_conditions.append(TrigramSimilarity('size', query))
        if not columns or 'vendor_name' in columns:
            similarity_conditions.append(TrigramSimilarity('vendor_name', query))
        
        if similarity_conditions:
            queryset = queryset.annotate(similarity=sum(similarity_conditions)).order_by('-similarity', 'item_number')
        else:
            queryset = queryset.order_by('item_number')
    else:
        # Basic SQLite similarity based on contains matches
        # Only calculate similarity for columns that were actually searched
        similarity_case = "CASE "
        params = []
        
        if not columns or 'item_number' in columns:
            similarity_case += "WHEN item_number LIKE %s THEN 4 "
            params.append(f'%{query}%')
        if not columns or 'description' in columns:
            similarity_case += "WHEN description LIKE %s THEN 3 "
            params.append(f'%{query}%')
        if not columns or 'size' in columns:
            similarity_case += "WHEN size LIKE %s THEN 2 "
            params.append(f'%{query}%')
        if not columns or 'vendor_name' in columns:
            similarity_case += "WHEN vendor_name LIKE %s THEN 1 "
            params.append(f'%{query}%')
        
        similarity_case += "ELSE 0 END"
        
        queryset = queryset.extra(
            select={'similarity': similarity_case},
            select_params=params
        ).order_by('-similarity', 'item_number')
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)
    
    # Format results
    results = []
    for part in page_obj:
        results.append({
            'id': part.id,
            'item_number': part.item_number,
            'description': part.description,
            'size': part.size,
            'product_group_id': part.product_group_id,
            'unit_cost': float(part.unit_cost) if part.unit_cost else None,
            'unit_cost_date': part.unit_cost_date.isoformat() if part.unit_cost_date else None,
            'vendor_name': part.vendor_name,
            'vendor_product_number': part.vendor_product_number,
            'vendor_product_description': part.vendor_product_description,
            'vendor_phone': part.vendor_phone,
            'similarity': round(part.similarity, 3) if hasattr(part, 'similarity') else 0,
            'last_updated': part.last_updated.isoformat()
        })
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # Return HTML for HTMX
        context = {
            'results': results,
            'total': paginator.count,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'query': query
        }
        return render(request, 'dynamics_search/search_results.html', context)
    else:
        # Return JSON for AJAX requests
        return JsonResponse({
            'results': results,
            'total': paginator.count,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'query': query
        })


def build_search_conditions(query, columns=None):
    """Build Q objects for search with wildcard support and column filtering"""
    print(f"=== BUILD SEARCH CONDITIONS DEBUG ===")
    print(f"Query: '{query}'")
    print(f"Columns: {columns}")
    
    conditions = Q()
    
    # Clean up the query - remove wildcard characters and split by spaces
    clean_query = query.replace('%', '').replace('*', '').strip()
    print(f"Clean query: '{clean_query}'")
    
    if not clean_query:
        print("No clean query - returning empty Q")
        return Q()  # Return empty Q if no valid search terms
    
    # Split by spaces for multiple terms
    terms = clean_query.split()
    print(f"Terms: {terms}")
    
    # Define available search fields
    search_fields = {
        'item_number': Q(item_number__icontains=''),
        'description': Q(description__icontains=''),
        'size': Q(size__icontains=''),
        'vendor_name': Q(vendor_name__icontains='')
    }
    
    # If no columns specified, search all fields (default behavior)
    if not columns:
        columns = list(search_fields.keys())
    
    print(f"Final columns to search: {columns}")
    
    for term in terms:
        if term:  # Only process non-empty terms
            term_conditions = Q()
            
            # Build conditions for each selected column (OR logic - match in any selected column)
            for column in columns:
                if column in search_fields:
                    if column == 'item_number':
                        term_conditions |= Q(item_number__icontains=term)
                    elif column == 'description':
                        term_conditions |= Q(description__icontains=term)
                    elif column == 'size':
                        term_conditions |= Q(size__icontains=term)
                    elif column == 'vendor_name':
                        term_conditions |= Q(vendor_name__icontains=term)
            
            # Add this term's conditions to the overall conditions (AND logic between terms)
            if term_conditions:
                conditions &= term_conditions
                print(f"Added term conditions for '{term}': {term_conditions}")
    
    print(f"Final search conditions: {conditions}")
    print(f"=== BUILD SEARCH CONDITIONS COMPLETE ===")
    return conditions


@require_http_methods(["GET"])
def search_suggestions(request):
    """Get search suggestions for autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Get suggestions from item_number and description
    suggestions = Part.objects.filter(
        Q(item_number__icontains=query) | 
        Q(description__icontains=query)
    ).values_list('item_number', 'description')[:10]
    
    # Format suggestions
    results = []
    seen = set()
    
    for item_number, description in suggestions:
        if item_number not in seen:
            results.append({
                'item_number': item_number,
                'description': description[:100] + '...' if len(description) > 100 else description
            })
            seen.add(item_number)
    
    return JsonResponse({'suggestions': results})


def part_detail(request, part_id):
    """Detail view for a specific part"""
    try:
        part = Part.objects.get(id=part_id)
        return render(request, 'dynamics_search/part_detail.html', {'part': part})
    except Part.DoesNotExist:
        return JsonResponse({'error': 'Part not found'}, status=404)