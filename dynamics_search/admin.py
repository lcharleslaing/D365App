from django.contrib import admin
from django.utils.html import format_html
from import_export import admin as import_export_admin
from .models import Part, SearchHistory
from .resources import PartResource


@admin.register(Part)
class PartAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = PartResource
    list_display = ['item_number', 'description_short', 'size', 'product_group_id', 'unit_cost', 'vendor_name', 'last_updated']
    list_filter = ['last_updated', 'size', 'product_group_id', 'vendor_name']
    search_fields = ['item_number', 'description', 'size', 'product_group_id', 'vendor_name', 'vendor_product_number']
    readonly_fields = ['last_updated', 'content_hash', 'search_vector']
    ordering = ['-last_updated']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('item_number', 'description', 'size', 'product_group_id')
        }),
        ('Cost Information', {
            'fields': ('unit_cost', 'unit_cost_date'),
            'classes': ('collapse',)
        }),
        ('Vendor Information', {
            'fields': ('vendor_name', 'vendor_product_number', 'vendor_product_description', 'vendor_phone'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('last_updated', 'content_hash', 'search_vector'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        """Display truncated description"""
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description
    description_short.short_description = 'Description'
    
    def similarity_score(self, obj):
        """Display similarity score if available"""
        if hasattr(obj, 'similarity'):
            score = int(obj.similarity * 100)
            color = 'green' if score > 80 else 'orange' if score > 50 else 'red'
            return format_html(
                '<span style="color: {};">{}%</span>',
                color, score
            )
        return '-'
    similarity_score.short_description = 'Similarity'
    
    def get_queryset(self, request):
        """Optimize queryset for admin"""
        return super().get_queryset(request).select_related()
    
    actions = ['refresh_search_vectors']
    
    def refresh_search_vectors(self, request, queryset):
        """Refresh search vectors for selected parts"""
        updated = 0
        for part in queryset:
            part.save()  # This will update the search_vector
            updated += 1
        
        self.message_user(
            request,
            f"Successfully refreshed search vectors for {updated} parts."
        )
    refresh_search_vectors.short_description = "Refresh search vectors"


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['query', 'columns_display', 'result_count', 'created_at', 'user_session']
    list_filter = ['created_at', 'result_count']
    search_fields = ['query', 'user_session']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Search Details', {
            'fields': ('query', 'columns', 'result_count')
        }),
        ('Session Information', {
            'fields': ('user_session', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset for admin"""
        return super().get_queryset(request)
    
    actions = ['clear_old_history']
    
    def clear_old_history(self, request, queryset):
        """Clear search history older than 30 days"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        old_history = SearchHistory.objects.filter(created_at__lt=cutoff_date)
        count = old_history.count()
        old_history.delete()
        
        self.message_user(
            request,
            f"Successfully deleted {count} old search history entries."
        )
    clear_old_history.short_description = "Clear old history (30+ days)"