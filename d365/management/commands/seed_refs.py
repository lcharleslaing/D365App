from django.core.management.base import BaseCommand

from d365.models import (
    HeaterMaterial, HeaterDiameter, HeaterHeight, StackDiameter, StackHeight,
    FlangeInlet, HeaterModelRef, GasTrainSize, GasTrainMount, BTURating,
    HeaterHandRef, HeaterABRef,
    TankMaterial, TankDiameter, TankHeight, TankHeightInches, TankType,
    PumpMaterial, PumpTypeRef, PumpPressure, SystemType, Horsepower,
)


class Command(BaseCommand):
    help = "Seed reference tables with provided lists"

    def handle(self, *args, **options):
        # Heater
        self._upsert(HeaterMaterial, [(c, c) for c in ['304', '316', 'AL6XN']], fields=('code', 'display_name'))
        self._upsert_values(HeaterDiameter, 'diameter_inch', [30, 42, 54, 60, 76, 84, 96])
        self._upsert_values(StackDiameter, 'diameter_inch', [12, 18, 24, 30, 36])
        self._upsert_values(StackHeight, 'height_ft', [9.5, 10, 12, 18, 24])
        self._upsert_values(HeaterHeight, 'height_ft', [7, 8, 8.5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
        self._upsert_values(FlangeInlet, 'size_inch', [1, 1.25, 1.5, 2, 2.5, 3, 4, 6])
        self._upsert(HeaterModelRef, [(c, c) for c in ['GP', 'RM', 'TE', 'TE-NSF']], fields=('code', 'display_name'))
        self._upsert_values(GasTrainSize, 'size_inch', [1, 1.5, 2, 2.5, 3])
        self._upsert(GasTrainMount, [('BM', 'BM'), ('FM', 'FM')], fields=('code', 'display_name'))
        self._upsert_values(BTURating, 'value_mmbtu', [1.2, 2, 3, 4.5, 5.5, 6, 7, 8, 9, 9.9, 10, 10.5, 11, 12, 12.5, 15, 18, 19, 20, 21, 25, 30])
        self._upsert(HeaterHandRef, [('LEFT', 'LEFT'), ('RIGHT', 'RIGHT')], fields=('code', 'display_name'))
        self._upsert(HeaterABRef, [(c, c) for c in ['', 'A', 'B', 'C', 'D', '1', '2', '3', '4']], fields=('code', 'display_name'))

        # Tank
        self._upsert(TankMaterial, [(c, c) for c in ['304', '316']], fields=('code', 'display_name'))
        self._upsert_values(TankDiameter, 'diameter_inch', [48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 132, 138, 144, 150, 156, 162, 168])
        self._upsert_values(TankHeight, 'height_ft', list(range(3, 36)))
        self._upsert_pairs(TankHeightInches, 'height_ft', 'inches', [
            (3, 36.25), (4, 48.25), (5, 60.25), (6, 72.25), (7, 83.5), (8, 95.5), (9, 107.5), (10, 119.5),
            (11, 131.5), (12, 143.5), (13, 154.75), (14, 166.75), (15, 178.75), (16, 190.75), (17, 202.75),
            (18, 214.75), (19, 226), (20, 238), (21, 250), (22, 262), (23, 274), (24, 286), (25, 297.25),
            (26, 309.25), (27, 321.25), (28, 333.25), (29, 345.25), (30, 357.25), (31, 368.5), (32, 380.5),
            (33, 392.5), (34, 404.5), (35, 416.5),
        ])
        self._upsert(TankType, [(c, c) for c in ['HW', 'TW', 'CW', 'CMF', 'RO', 'WW', 'EQ']], fields=('code', 'display_name'))

        # Pump
        self._upsert(PumpMaterial, [(c, c) for c in ['304', '316']], fields=('code', 'display_name'))
        self._upsert(PumpTypeRef, [(c, c) for c in ['SIMPLEX', 'DUPLEX', 'TRIPLEX', 'QUADPLEX']], fields=('code', 'display_name'))
        self._upsert(PumpPressure, [(c, c) for c in ['LP', 'MP', 'HP']], fields=('code', 'display_name'))
        self._upsert(SystemType, [(c, c) for c in ['HW', 'TW', 'CW', 'CMF', 'RO', 'WW']], fields=('code', 'display_name'))
        self._upsert_values(Horsepower, 'hp', [0.5, 0.75, 1, 2, 3, 5, 7.5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100])

        self.stdout.write(self.style.SUCCESS('Reference tables seeded.'))

    def _upsert_values(self, model, field, values):
        for v in values:
            model.objects.update_or_create(**{field: v})

    def _upsert(self, model, pairs, fields=('code', 'display_name')):
        code_f, disp_f = fields
        for code, disp in pairs:
            model.objects.update_or_create(**{code_f: code}, defaults={disp_f: disp})

    def _upsert_pairs(self, model, key_field, value_field, pairs):
        for k, v in pairs:
            model.objects.update_or_create(**{key_field: k}, defaults={value_field: v})


