from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import re

from .models import Part, SearchHistory

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
        if not columns or 'product_group_id' in columns:
            similarity_case += "WHEN product_group_id LIKE %s THEN 1 "
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
    
    # Save search to history (only for successful searches with results)
    if results and len(results) > 0:
        # Get or create a simple session identifier
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        # Save search history
        SearchHistory.objects.create(
            query=query,
            columns=columns,
            result_count=paginator.count,
            user_session=session_key
        )
    
    # Check if this is a JSON request (explicitly requested)
    if request.headers.get('Accept') == 'application/json' and not request.headers.get('HX-Request'):
        # Return JSON only when explicitly requested
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
    else:
        # Return HTML for all other requests (HTMX, direct access, etc.)
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


def build_search_conditions(query, columns=None):
    """Build Q objects for search with wildcard support and column filtering"""
    conditions = Q()
    
    if not query.strip():
        return Q()  # Return empty Q if no valid search terms
    
    # Split by spaces for multiple terms, but preserve wildcards within each term
    terms = query.strip().split()
    
    # Define available search fields
    search_fields = {
        'item_number': Q(item_number__icontains=''),
        'description': Q(description__icontains=''),
        'size': Q(size__icontains=''),
        'vendor_name': Q(vendor_name__icontains=''),
        'product_group_id': Q(product_group_id__icontains='')
    }
    
    # If no columns specified, search all fields (default behavior)
    if not columns:
        columns = list(search_fields.keys())
    
    for term in terms:
        if term:  # Only process non-empty terms
            term_conditions = Q()
            
            # Check if term contains multiple wildcards (like *ss316*tubes*)
            # Simple wildcards like *ss316* should use icontains, complex ones use regex
            has_multiple_wildcards = term.count('*') > 2 or (term.count('*') == 2 and not (term.startswith('*') and term.endswith('*')))
            
            if has_multiple_wildcards:
                # Use icontains for complex wildcard matching (like *ss316*stack*media*)
                # Extract all terms between * wildcards and search for each one
                # Split by * and filter out empty strings
                wildcard_terms = [t for t in term.split('*') if t.strip()]
                
                # Build conditions for each selected column (OR logic - match in any selected column)
                for column in columns:
                    if column in search_fields:
                        column_conditions = Q()
                        # Each term must be present (AND logic between terms)
                        for wildcard_term in wildcard_terms:
                            if column == 'item_number':
                                column_conditions &= Q(item_number__icontains=wildcard_term)
                            elif column == 'description':
                                column_conditions &= Q(description__icontains=wildcard_term)
                            elif column == 'size':
                                column_conditions &= Q(size__icontains=wildcard_term)
                            elif column == 'vendor_name':
                                column_conditions &= Q(vendor_name__icontains=wildcard_term)
                            elif column == 'product_group_id':
                                column_conditions &= Q(product_group_id__icontains=wildcard_term)
                        term_conditions |= column_conditions
            else:
                # Use icontains for simple wildcard matching (like *ss316* or ss316)
                # Remove * wildcards for icontains
                clean_term = term.replace('*', '')
                
                # Build conditions for each selected column (OR logic - match in any selected column)
                for column in columns:
                    if column in search_fields:
                        if column == 'item_number':
                            term_conditions |= Q(item_number__icontains=clean_term)
                        elif column == 'description':
                            term_conditions |= Q(description__icontains=clean_term)
                        elif column == 'size':
                            term_conditions |= Q(size__icontains=clean_term)
                        elif column == 'vendor_name':
                            term_conditions |= Q(vendor_name__icontains=clean_term)
                        elif column == 'product_group_id':
                            term_conditions |= Q(product_group_id__icontains=clean_term)
            
            # Add this term's conditions to the overall conditions (AND logic between terms)
            if term_conditions:
                conditions &= term_conditions
    
    return conditions


@require_http_methods(["GET"])
def search_history_api(request):
    """API endpoint to get search history for current session"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'history': []})
    
    # Get recent search history (last 50 searches)
    history = SearchHistory.objects.filter(user_session=session_key)[:50]
    
    history_data = []
    for search in history:
        history_data.append({
            'id': search.id,
            'query': search.query,
            'columns': search.columns,
            'columns_display': search.columns_display,
            'result_count': search.result_count,
            'created_at': search.created_at.isoformat(),
            'time_ago': _time_ago(search.created_at)
        })
    
    return JsonResponse({'history': history_data})


@require_http_methods(["DELETE"])
@csrf_exempt
def delete_search_history(request, history_id):
    """API endpoint to delete a specific search history entry"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'success': False, 'error': 'No session'}, status=400)
    
    try:
        search = SearchHistory.objects.get(id=history_id, user_session=session_key)
        search.delete()
        return JsonResponse({'success': True})
    except SearchHistory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Search not found'}, status=404)


@require_http_methods(["DELETE"])
@csrf_exempt
def clear_all_history(request):
    """API endpoint to clear all search history for current session"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'success': False, 'error': 'No session'}, status=400)
    
    deleted_count = SearchHistory.objects.filter(user_session=session_key).delete()[0]
    return JsonResponse({'success': True, 'deleted_count': deleted_count})


def _time_ago(created_at):
    """Helper function to format time ago"""
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    diff = now - created_at
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


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