from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, DateTimeWidget
from .models import (
    D365Job, D365Heater, D365Tank, D365Pump, D365GeneratedItem,
    HeaterMaterial, HeaterDiameter, HeaterHeight, StackDiameter, StackHeight,
    FlangeInlet, HeaterModelRef, GasTrainSize, GasTrainMount, BTURating,
    HeaterHandRef, TankMaterial, HeaterABRef, TankDiameter, TankHeight,
    TankHeightInches, TankType, PumpMaterial, PumpTypeRef, PumpPressure,
    SystemType, Horsepower
)


class D365JobResource(resources.ModelResource):
    class Meta:
        model = D365Job
        fields = ('id', 'job_number', 'job_name', 'created_at', 'updated_at')
        export_order = ('id', 'job_number', 'job_name', 'created_at', 'updated_at')
        import_id_fields = ('job_number',)


class D365HeaterResource(resources.ModelResource):
    class Meta:
        model = D365Heater
        fields = (
            'id', 'job_number', 'dash_number', 'heater_diameter', 'heater_height',
            'stack_diameter', 'stack_height', 'flange_inlet', 'heater_model',
            'material', 'gas_train_size', 'gas_train_mount', 'btu', 'hand',
            'heater_ab', 'heater_single_dual', 'created_at'
        )
        export_order = (
            'id', 'job_number', 'dash_number', 'heater_diameter', 'heater_height',
            'stack_diameter', 'stack_height', 'flange_inlet', 'heater_model',
            'material', 'gas_train_size', 'gas_train_mount', 'btu', 'hand',
            'heater_ab', 'heater_single_dual', 'created_at'
        )
        import_id_fields = ('job_number', 'dash_number')


class D365TankResource(resources.ModelResource):
    class Meta:
        model = D365Tank
        fields = (
            'id', 'job_number', 'dash_number', 'tank_diameter', 'tank_height',
            'tank_height_inches', 'tank_material', 'tank_type', 'created_at'
        )
        export_order = (
            'id', 'job_number', 'dash_number', 'tank_diameter', 'tank_height',
            'tank_height_inches', 'tank_material', 'tank_type', 'created_at'
        )
        import_id_fields = ('job_number', 'dash_number')


class D365PumpResource(resources.ModelResource):
    class Meta:
        model = D365Pump
        fields = (
            'id', 'job_number', 'dash_number', 'pump_type', 'pump_material',
            'pump_pressure', 'system_type', 'horsepower', 'skid_length',
            'skid_width', 'skid_height', 'created_at'
        )
        export_order = (
            'id', 'job_number', 'dash_number', 'pump_type', 'pump_material',
            'pump_pressure', 'system_type', 'horsepower', 'skid_length',
            'skid_width', 'skid_height', 'created_at'
        )
        import_id_fields = ('job_number', 'dash_number')


class D365GeneratedItemResource(resources.ModelResource):
    class Meta:
        model = D365GeneratedItem
        fields = (
            'id', 'job_number', 'section', 'item_number', 'description',
            'bom', 'template', 'product_type', 'created_at'
        )
        export_order = (
            'id', 'job_number', 'section', 'item_number', 'description',
            'bom', 'template', 'product_type', 'created_at'
        )
        import_id_fields = ('job_number', 'section', 'item_number')


# Reference data resources
class HeaterMaterialResource(resources.ModelResource):
    class Meta:
        model = HeaterMaterial
        fields = ('id', 'code', 'display_name')
        export_order = ('id', 'code', 'display_name')


class HeaterDiameterResource(resources.ModelResource):
    class Meta:
        model = HeaterDiameter
        fields = ('id', 'diameter')
        export_order = ('id', 'diameter')


class HeaterHeightResource(resources.ModelResource):
    class Meta:
        model = HeaterHeight
        fields = ('id', 'height_ft')
        export_order = ('id', 'height_ft')


class StackDiameterResource(resources.ModelResource):
    class Meta:
        model = StackDiameter
        fields = ('id', 'diameter')
        export_order = ('id', 'diameter')


class StackHeightResource(resources.ModelResource):
    class Meta:
        model = StackHeight
        fields = ('id', 'height_ft')
        export_order = ('id', 'height_ft')


class FlangeInletResource(resources.ModelResource):
    class Meta:
        model = FlangeInlet
        fields = ('id', 'inlet')
        export_order = ('id', 'inlet')


class HeaterModelRefResource(resources.ModelResource):
    class Meta:
        model = HeaterModelRef
        fields = ('id', 'code', 'display_name')
        export_order = ('id', 'code', 'display_name')


class GasTrainSizeResource(resources.ModelResource):
    class Meta:
        model = GasTrainSize
        fields = ('id', 'size')
        export_order = ('id', 'size')


class GasTrainMountResource(resources.ModelResource):
    class Meta:
        model = GasTrainMount
        fields = ('id', 'mount')
        export_order = ('id', 'mount')


class BTURatingResource(resources.ModelResource):
    class Meta:
        model = BTURating
        fields = ('id', 'btu')
        export_order = ('id', 'btu')


class HeaterHandRefResource(resources.ModelResource):
    class Meta:
        model = HeaterHandRef
        fields = ('id', 'code', 'display_name')
        export_order = ('id', 'code', 'display_name')


class TankMaterialResource(resources.ModelResource):
    class Meta:
        model = TankMaterial
        fields = ('id', 'code', 'display_name')
        export_order = ('id', 'code', 'display_name')


class HeaterABRefResource(resources.ModelResource):
    class Meta:
        model = HeaterABRef
        fields = ('id', 'code', 'display_name')
        export_order = ('id', 'code', 'display_name')


class TankDiameterResource(resources.ModelResource):
    class Meta:
        model = TankDiameter
        fields = ('id', 'diameter')
        export_order = ('id', 'diameter')


class TankHeightResource(resources.ModelResource):
    class Meta:
        model = TankHeight
        fields = ('id', 'height_ft')
        export_order = ('id', 'height_ft')


class TankHeightInchesResource(resources.ModelResource):
    class Meta:
        model = TankHeightInches
        fields = ('id', 'height_inches')
        export_order = ('id', 'height_inches')


class TankTypeResource(resources.ModelResource):
    class Meta:
        model = TankType
        fields = ('id', 'type')
        export_order = ('id', 'type')


class PumpMaterialResource(resources.ModelResource):
    class Meta:
        model = PumpMaterial
        fields = ('id', 'code', 'display_name')
        export_order = ('id', 'code', 'display_name')


class PumpTypeRefResource(resources.ModelResource):
    class Meta:
        model = PumpTypeRef
        fields = ('id', 'code', 'display_name')
        export_order = ('id', 'code', 'display_name')


class PumpPressureResource(resources.ModelResource):
    class Meta:
        model = PumpPressure
        fields = ('id', 'pressure')
        export_order = ('id', 'pressure')


class SystemTypeResource(resources.ModelResource):
    class Meta:
        model = SystemType
        fields = ('id', 'type')
        export_order = ('id', 'type')


class HorsepowerResource(resources.ModelResource):
    class Meta:
        model = Horsepower
        fields = ('id', 'hp')
        export_order = ('id', 'hp')
