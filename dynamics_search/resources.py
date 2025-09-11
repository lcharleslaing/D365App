from import_export import resources
from .models import Part


class PartResource(resources.ModelResource):
    class Meta:
        model = Part
        fields = (
            'id', 'item_number', 'description', 'size', 'product_group_id',
            'unit_cost', 'unit_cost_date', 'vendor_name', 'vendor_product_number',
            'vendor_product_description', 'vendor_phone', 'last_updated'
        )
        export_order = (
            'id', 'item_number', 'description', 'size', 'product_group_id',
            'unit_cost', 'unit_cost_date', 'vendor_name', 'vendor_product_number',
            'vendor_product_description', 'vendor_phone', 'last_updated'
        )
        import_id_fields = ('item_number',)
        
    def before_import_row(self, row, **kwargs):
        """Clean up data before import"""
        from datetime import datetime
        
        # Clean up item_number
        if 'item_number' in row and row['item_number']:
            row['item_number'] = str(row['item_number']).strip()
        
        # Clean up description
        if 'description' in row and row['description']:
            row['description'] = str(row['description']).strip()
        
        # Clean up size
        if 'size' in row and row['size']:
            row['size'] = str(row['size']).strip()
        
        # Clean up product_group_id
        if 'product_group_id' in row and row['product_group_id']:
            row['product_group_id'] = str(row['product_group_id']).strip()
        
        # Clean up unit_cost
        if 'unit_cost' in row and row['unit_cost']:
            try:
                row['unit_cost'] = float(row['unit_cost'])
            except (ValueError, TypeError):
                row['unit_cost'] = None
        
        # Parse unit_cost_date
        if 'unit_cost_date' in row and row['unit_cost_date']:
            try:
                # Handle various date formats
                date_str = str(row['unit_cost_date']).strip()
                if date_str and date_str != '1/1/1900 12:00':  # Skip default empty dates
                    # Try different date formats
                    for fmt in ['%m/%d/%Y %H:%M', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                        try:
                            row['unit_cost_date'] = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        row['unit_cost_date'] = None
                else:
                    row['unit_cost_date'] = None
            except (ValueError, TypeError):
                row['unit_cost_date'] = None
        
        # Clean up vendor fields
        if 'vendor_name' in row and row['vendor_name']:
            row['vendor_name'] = str(row['vendor_name']).strip()
        
        if 'vendor_product_number' in row and row['vendor_product_number']:
            row['vendor_product_number'] = str(row['vendor_product_number']).strip()
        
        if 'vendor_product_description' in row and row['vendor_product_description']:
            row['vendor_product_description'] = str(row['vendor_product_description']).strip()
        
        if 'vendor_phone' in row and row['vendor_phone']:
            row['vendor_phone'] = str(row['vendor_phone']).strip()
    
    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip rows with validation errors"""
        if import_validation_errors:
            return True
        return False
