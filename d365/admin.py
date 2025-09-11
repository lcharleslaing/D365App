from django.contrib import admin
from import_export import admin as import_export_admin
from . import models
from .resources import (
    D365JobResource, D365HeaterResource, D365TankResource, D365PumpResource,
    D365GeneratedItemResource, HeaterMaterialResource, HeaterDiameterResource,
    HeaterHeightResource, StackDiameterResource, StackHeightResource,
    FlangeInletResource, HeaterModelRefResource, GasTrainSizeResource,
    GasTrainMountResource, BTURatingResource, HeaterHandRefResource,
    TankMaterialResource, HeaterABRefResource, TankDiameterResource,
    TankHeightResource, TankHeightInchesResource, TankTypeResource,
    PumpMaterialResource, PumpTypeRefResource, PumpPressureResource,
    SystemTypeResource, HorsepowerResource
)


@admin.register(models.D365Job)
class D365JobAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = D365JobResource
    list_display = ('job_number', 'job_name', 'updated_at')
    search_fields = ('job_number', 'job_name')
    list_filter = ('created_at', 'updated_at')


@admin.register(models.D365Heater)
class D365HeaterAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = D365HeaterResource
    list_display = ('job_number', 'dash_number', 'material', 'heater_diameter', 'heater_height')
    search_fields = ('job_number',)
    list_filter = ('material', 'heater_diameter', 'heater_height', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(models.D365Tank)
class D365TankAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = D365TankResource
    list_display = ('job_number', 'dash_number', 'material', 'tank_diameter', 'tank_height')
    search_fields = ('job_number',)
    list_filter = ('material', 'tank_type', 'tank_diameter', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(models.D365Pump)
class D365PumpAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = D365PumpResource
    list_display = ('job_number', 'dash_number', 'pump_type', 'hp', 'material')
    search_fields = ('job_number',)
    list_filter = ('pump_type', 'pump_pressure', 'system_type', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(models.D365GeneratedItem)
class D365GeneratedItemAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = D365GeneratedItemResource
    list_display = ('job_number', 'section', 'item_number', 'description', 'created_at')
    search_fields = ('job_number', 'item_number', 'description')
    list_filter = ('section', 'bom', 'template', 'product_type', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


# Reference models with import/export
@admin.register(models.HeaterMaterial)
class HeaterMaterialAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = HeaterMaterialResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.HeaterDiameter)
class HeaterDiameterAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = HeaterDiameterResource
    list_display = ('diameter_inch',)
    search_fields = ('diameter_inch',)


@admin.register(models.HeaterHeight)
class HeaterHeightAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = HeaterHeightResource
    list_display = ('height_ft',)
    search_fields = ('height_ft',)


@admin.register(models.StackDiameter)
class StackDiameterAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = StackDiameterResource
    list_display = ('diameter_inch',)
    search_fields = ('diameter_inch',)


@admin.register(models.StackHeight)
class StackHeightAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = StackHeightResource
    list_display = ('height_ft',)
    search_fields = ('height_ft',)


@admin.register(models.FlangeInlet)
class FlangeInletAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = FlangeInletResource
    list_display = ('size_inch',)
    search_fields = ('size_inch',)


@admin.register(models.HeaterModelRef)
class HeaterModelRefAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = HeaterModelRefResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.GasTrainSize)
class GasTrainSizeAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = GasTrainSizeResource
    list_display = ('size_inch',)
    search_fields = ('size_inch',)


@admin.register(models.GasTrainMount)
class GasTrainMountAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = GasTrainMountResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.BTURating)
class BTURatingAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = BTURatingResource
    list_display = ('value_mmbtu',)
    search_fields = ('value_mmbtu',)


@admin.register(models.HeaterHandRef)
class HeaterHandRefAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = HeaterHandRefResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.TankMaterial)
class TankMaterialAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = TankMaterialResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.HeaterABRef)
class HeaterABRefAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = HeaterABRefResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.TankDiameter)
class TankDiameterAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = TankDiameterResource
    list_display = ('diameter_inch',)
    search_fields = ('diameter_inch',)


@admin.register(models.TankHeight)
class TankHeightAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = TankHeightResource
    list_display = ('height_ft',)
    search_fields = ('height_ft',)


@admin.register(models.TankHeightInches)
class TankHeightInchesAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = TankHeightInchesResource
    list_display = ('height_ft', 'inches')
    search_fields = ('height_ft', 'inches')


@admin.register(models.TankType)
class TankTypeAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = TankTypeResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.PumpMaterial)
class PumpMaterialAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = PumpMaterialResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.PumpTypeRef)
class PumpTypeRefAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = PumpTypeRefResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.PumpPressure)
class PumpPressureAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = PumpPressureResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.SystemType)
class SystemTypeAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = SystemTypeResource
    list_display = ('code', 'display_name')
    search_fields = ('code', 'display_name')


@admin.register(models.Horsepower)
class HorsepowerAdmin(import_export_admin.ImportExportModelAdmin):
    resource_class = HorsepowerResource
    list_display = ('hp',)
    search_fields = ('hp',)

# Register your models here.
