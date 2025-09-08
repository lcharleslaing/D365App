from django.db import models
from django.utils import timezone


class D365Job(models.Model):
    job_number = models.CharField(max_length=64, unique=True)
    job_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.job_number} - {self.job_name or ''}".strip()


class D365Heater(models.Model):
    job_number = models.CharField(max_length=64)
    dash_number = models.CharField(max_length=32, blank=True, null=True)

    heater_diameter = models.IntegerField()
    heater_height = models.FloatField()
    stack_diameter = models.IntegerField()
    stack_height = models.FloatField(blank=True, null=True)

    flange_inlet = models.FloatField()
    heater_model = models.CharField(max_length=32)
    material = models.CharField(max_length=32)

    gas_train_size = models.FloatField()
    gas_train_mount = models.CharField(max_length=8)

    btu = models.FloatField()
    hand = models.CharField(max_length=16)

    heater_ab = models.CharField(max_length=8)
    heater_single_dual = models.CharField(max_length=8)

    created_at = models.DateTimeField(default=timezone.now)

    def generate_items(self, stack_height: float | None = None) -> list[dict]:
        items: list[dict] = []
        job = self.job_number
        dash = self.dash_number or ''
        stack_h = stack_height if stack_height is not None else self.heater_height

        def line(item_number: str, description: str, bom: str, template: str, product_type: str) -> dict:
            return {
                'item_number': item_number,
                'description': description,
                'bom': bom,
                'template': template,
                'product_type': product_type,
            }

        items.append(line(
            f"{job}-HEAT-{dash}",
            f"Heater Main Assembly {self.heater_model} {self.material}",
            "HEATER-MAIN",
            "HEATER-TEMPLATE",
            "Finished Good",
        ))
        items.append(line(
            f"{job}-HEAT-WELD-{dash}",
            f"Heater Weld Assembly {self.heater_diameter}x{self.heater_height}",
            "HEATER-WELD",
            "HEATER-WELD-TEMPLATE",
            "Subassembly",
        ))
        items.append(line(
            f"{job}-SHELL-{dash}",
            f"Shell {self.material} {self.heater_diameter} DIA",
            "SHELL",
            "SHELL-TEMPLATE",
            "Raw Material",
        ))
        items.append(line(
            f"{job}-STACK-{dash}",
            f"Stack {self.material} {self.stack_diameter} DIA x {stack_h}",
            "STACK",
            "STACK-TEMPLATE",
            "Subassembly",
        ))
        items.append(line(
            f"{job}-GASTRAIN-{dash}",
            f"Gas Train {self.gas_train_mount} {self.gas_train_size} in",
            "GAS-TRAIN",
            "GAS-TRAIN-TEMPLATE",
            "Purchased",
        ))
        items.append(line(
            f"{job}-MODPIPING-{dash}",
            f"Mod Piping {self.flange_inlet} in",
            "MOD-PIPING",
            "MOD-PIPING-TEMPLATE",
            "Subassembly",
        ))
        items.append(line(
            f"{job}-PRECUT-{dash}",
            f"Precut Plate for Heater",
            "PRECUT",
            "PRECUT-TEMPLATE",
            "Raw Material",
        ))
        return items


class D365Tank(models.Model):
    job_number = models.CharField(max_length=64)
    dash_number = models.CharField(max_length=32, blank=True, null=True)

    tank_diameter = models.IntegerField()
    tank_height = models.IntegerField()
    tank_inches = models.FloatField()

    material = models.CharField(max_length=32)
    tank_type = models.CharField(max_length=16)

    created_at = models.DateTimeField(default=timezone.now)

    def generate_items(self) -> list[dict]:
        job = self.job_number
        dash = self.dash_number or ''
        return [
            {
                'item_number': f"{job}-TANK-{dash}",
                'description': f"Tank {self.material} {self.tank_diameter} DIA x {self.tank_height} ft",
                'bom': 'TANK-MAIN',
                'template': 'TANK-TEMPLATE',
                'product_type': 'Finished Good',
            },
            {
                'item_number': f"{job}-TANK-SHELL-{dash}",
                'description': f"Tank Shell {self.material} {self.tank_diameter} DIA",
                'bom': 'TANK-SHELL',
                'template': 'TANK-SHELL-TEMPLATE',
                'product_type': 'Raw Material',
            },
            {
                'item_number': f"{job}-TANK-PRECUT-{dash}",
                'description': "Precut Plate for Tank",
                'bom': 'PRECUT',
                'template': 'PRECUT-TEMPLATE',
                'product_type': 'Raw Material',
            },
        ]


class D365Pump(models.Model):
    job_number = models.CharField(max_length=64)
    dash_number = models.CharField(max_length=32, blank=True, null=True)

    pump_type = models.CharField(max_length=16)
    pump_pressure = models.CharField(max_length=8)
    system_type = models.CharField(max_length=8)

    hp = models.FloatField()
    material = models.CharField(max_length=32)

    skid_length = models.FloatField()
    skid_width = models.FloatField()
    skid_height = models.FloatField()

    created_at = models.DateTimeField(default=timezone.now)

    def generate_items(self) -> list[dict]:
        job = self.job_number
        dash = self.dash_number or ''
        thickness_map = {
            'SIMPLEX': 0.25,
            'DUPLEX': 0.375,
            'TRIPLEX': 0.5,
            'QUADPLEX': 0.5,
        }
        precut_thickness = thickness_map.get(self.pump_type.upper(), 0.25)
        return [
            {
                'item_number': f"{job}-PUMP-{dash}",
                'description': f"Pump {self.pump_type} {self.hp} HP {self.material}",
                'bom': 'PUMP-MAIN',
                'template': 'PUMP-TEMPLATE',
                'product_type': 'Finished Good',
            },
            {
                'item_number': f"{job}-SKID-{dash}",
                'description': f"Skid {self.skid_length}x{self.skid_width}x{self.skid_height}",
                'bom': 'SKID',
                'template': 'SKID-TEMPLATE',
                'product_type': 'Subassembly',
            },
            {
                'item_number': f"{job}-PRECUT-{dash}",
                'description': f"Precut Plate {precut_thickness} in",
                'bom': 'PRECUT',
                'template': 'PRECUT-TEMPLATE',
                'product_type': 'Raw Material',
            },
        ]


class D365StackEconomizer(models.Model):
    job_number = models.CharField(max_length=64)
    dash_number = models.CharField(max_length=32, blank=True, null=True)
    diameter = models.IntegerField()
    height = models.IntegerField()
    material = models.CharField(max_length=32)
    created_at = models.DateTimeField(default=timezone.now)

    def generate_items(self) -> list[dict]:
        job = self.job_number
        dash = self.dash_number or ''
        return [
            {
                'item_number': f"{job}-ECON-{dash}",
                'description': f"Economizer {self.material} {self.diameter} DIA x {self.height}",
                'bom': 'ECON-MAIN',
                'template': 'ECON-TEMPLATE',
                'product_type': 'Finished Good',
            }
        ]


# Reference tables (from Excel Table Data Ref)

class HeaterMaterial(models.Model):
    code = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=64)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class HeaterDiameter(models.Model):
    diameter_inch = models.IntegerField(unique=True)

    class Meta:
        ordering = ['diameter_inch']

    def __str__(self) -> str:
        return f"{self.diameter_inch}"


class HeaterHeight(models.Model):
    height_ft = models.FloatField(unique=True)

    class Meta:
        ordering = ['height_ft']

    def __str__(self) -> str:
        return f"{self.height_ft}"


class StackDiameter(models.Model):
    diameter_inch = models.IntegerField(unique=True)

    class Meta:
        ordering = ['diameter_inch']

    def __str__(self) -> str:
        return f"{self.diameter_inch}"


class StackHeight(models.Model):
    height_ft = models.FloatField(unique=True)

    class Meta:
        ordering = ['height_ft']

    def __str__(self) -> str:
        return f"{self.height_ft}"


class FlangeInlet(models.Model):
    size_inch = models.FloatField(unique=True)

    class Meta:
        ordering = ['size_inch']

    def __str__(self) -> str:
        return f"{self.size_inch}"


class HeaterModelRef(models.Model):
    code = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=64)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class GasTrainSize(models.Model):
    size_inch = models.FloatField(unique=True)

    class Meta:
        ordering = ['size_inch']

    def __str__(self) -> str:
        return f"{self.size_inch}"


class GasTrainMount(models.Model):
    code = models.CharField(max_length=8, unique=True)
    display_name = models.CharField(max_length=32)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class BTURating(models.Model):
    value_mmbtu = models.FloatField(unique=True)

    class Meta:
        ordering = ['value_mmbtu']

    def __str__(self) -> str:
        return f"{self.value_mmbtu}"


class HeaterHandRef(models.Model):
    code = models.CharField(max_length=16, unique=True)
    display_name = models.CharField(max_length=32)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class TankMaterial(models.Model):
    code = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=64)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class HeaterABRef(models.Model):
    code = models.CharField(max_length=8, unique=True)
    display_name = models.CharField(max_length=16)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class TankDiameter(models.Model):
    diameter_inch = models.IntegerField(unique=True)

    class Meta:
        ordering = ['diameter_inch']

    def __str__(self) -> str:
        return f"{self.diameter_inch}"


class TankHeight(models.Model):
    height_ft = models.IntegerField(unique=True)

    class Meta:
        ordering = ['height_ft']

    def __str__(self) -> str:
        return f"{self.height_ft}"


class TankHeightInches(models.Model):
    height_ft = models.IntegerField(unique=True)
    inches = models.FloatField()

    class Meta:
        ordering = ['height_ft']

    def __str__(self) -> str:
        return f"{self.height_ft} ft -> {self.inches} in"


class TankType(models.Model):
    code = models.CharField(max_length=16, unique=True)
    display_name = models.CharField(max_length=32)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class PumpMaterial(models.Model):
    code = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=64)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class PumpTypeRef(models.Model):
    code = models.CharField(max_length=16, unique=True)
    display_name = models.CharField(max_length=32)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class PumpPressure(models.Model):
    code = models.CharField(max_length=8, unique=True)
    display_name = models.CharField(max_length=32)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class SystemType(models.Model):
    code = models.CharField(max_length=8, unique=True)
    display_name = models.CharField(max_length=32)

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return self.display_name


class Horsepower(models.Model):
    hp = models.FloatField(unique=True)

    class Meta:
        ordering = ['hp']

    def __str__(self) -> str:
        return f"{self.hp}"


# Create your models here.
