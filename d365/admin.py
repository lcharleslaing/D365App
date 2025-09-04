from django.contrib import admin
from . import models


@admin.register(models.D365Job)
class D365JobAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'job_name', 'updated_at')
    search_fields = ('job_number', 'job_name')


@admin.register(models.D365Heater)
class D365HeaterAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'dash_number', 'material', 'heater_diameter', 'heater_height')
    search_fields = ('job_number',)
    list_filter = ('material',)


@admin.register(models.D365Tank)
class D365TankAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'dash_number', 'material', 'tank_diameter', 'tank_height')
    search_fields = ('job_number',)
    list_filter = ('material', 'tank_type')


@admin.register(models.D365Pump)
class D365PumpAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'dash_number', 'pump_type', 'hp', 'material')
    search_fields = ('job_number',)
    list_filter = ('pump_type', 'pump_pressure', 'system_type')


reference_models = [
    models.HeaterMaterial,
    models.HeaterDiameter,
    models.HeaterHeight,
    models.StackDiameter,
    models.StackHeight,
    models.FlangeInlet,
    models.HeaterModelRef,
    models.GasTrainSize,
    models.GasTrainMount,
    models.BTURating,
    models.HeaterHandRef,
    models.HeaterABRef,
    models.TankMaterial,
    models.TankDiameter,
    models.TankHeight,
    models.TankHeightInches,
    models.TankType,
    models.PumpMaterial,
    models.PumpTypeRef,
    models.PumpPressure,
    models.SystemType,
    models.Horsepower,
]

for m in reference_models:
    admin.site.register(m)

# Register your models here.
