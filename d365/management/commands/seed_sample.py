from django.core.management.base import BaseCommand
from django.utils import timezone

from d365.models import (
    D365Job,
    D365Heater,
    D365Tank,
    D365Pump,
)


class Command(BaseCommand):
    help = "Seed sample D365 jobs with Heater, Tank, and Pump records"

    def handle(self, *args, **options):
        samples = [
            {
                'job_number': 'K-1001',
                'job_name': 'HW Heater + Tank + Pump',
                'heater': {
                    'dash_number': '01', 'heater_diameter': 72, 'heater_height': 12.0, 'stack_diameter': 18,
                    'flange_inlet': 2.0, 'heater_model': 'GP', 'material': '304',
                    'gas_train_size': 2.0, 'gas_train_mount': 'FM', 'btu': 4.0, 'hand': 'LH',
                    'heater_ab': 'A', 'heater_single_dual': 'S',
                },
                'tank': {
                    'dash_number': '01', 'tank_diameter': 96, 'tank_height': 12, 'tank_inches': 144.0,
                    'material': '304', 'tank_type': 'HW',
                },
                'pump': {
                    'dash_number': '01', 'pump_type': 'DUPLEX', 'pump_pressure': 'MP', 'system_type': 'HW',
                    'hp': 15.0, 'material': '304', 'skid_length': 120.0, 'skid_width': 48.0, 'skid_height': 24.0,
                },
            },
            {
                'job_number': 'K-1002',
                'job_name': 'TW Basic Config',
                'heater': {
                    'dash_number': '02', 'heater_diameter': 60, 'heater_height': 10.0, 'stack_diameter': 16,
                    'flange_inlet': 1.5, 'heater_model': 'RM', 'material': '316',
                    'gas_train_size': 1.5, 'gas_train_mount': 'BM', 'btu': 2.5, 'hand': 'RH',
                    'heater_ab': 'B', 'heater_single_dual': 'S',
                },
                'tank': {
                    'dash_number': '02', 'tank_diameter': 72, 'tank_height': 10, 'tank_inches': 120.0,
                    'material': '316', 'tank_type': 'TW',
                },
                'pump': {
                    'dash_number': '02', 'pump_type': 'SIMPLEX', 'pump_pressure': 'LP', 'system_type': 'TW',
                    'hp': 7.5, 'material': '316', 'skid_length': 96.0, 'skid_width': 36.0, 'skid_height': 20.0,
                },
            },
            {
                'job_number': 'K-1003',
                'job_name': 'RO High Pressure',
                'heater': {
                    'dash_number': '03', 'heater_diameter': 84, 'heater_height': 14.0, 'stack_diameter': 20,
                    'flange_inlet': 2.5, 'heater_model': 'TE', 'material': 'AL6XN',
                    'gas_train_size': 2.5, 'gas_train_mount': 'FM', 'btu': 8.0, 'hand': 'LH',
                    'heater_ab': 'A', 'heater_single_dual': 'D',
                },
                'tank': {
                    'dash_number': '03', 'tank_diameter': 120, 'tank_height': 20, 'tank_inches': 240.0,
                    'material': '304', 'tank_type': 'RO',
                },
                'pump': {
                    'dash_number': '03', 'pump_type': 'TRIPLEX', 'pump_pressure': 'HP', 'system_type': 'RO',
                    'hp': 30.0, 'material': '304', 'skid_length': 144.0, 'skid_width': 60.0, 'skid_height': 30.0,
                },
            },
        ]

        created_jobs = 0
        for s in samples:
            job, _ = D365Job.objects.update_or_create(
                job_number=s['job_number'],
                defaults={'job_name': s['job_name'], 'updated_at': timezone.now()}
            )

            D365Heater.objects.create(job_number=job.job_number, **s['heater'])
            D365Tank.objects.create(job_number=job.job_number, **s['tank'])
            D365Pump.objects.create(job_number=job.job_number, **s['pump'])
            created_jobs += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_jobs} sample jobs."))


