import csv
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from e24_app.models import Prediction

class Command(BaseCommand):
    help = 'Export all current predictions to a CSV file with start and end times'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='predictions_export.csv', help='Output CSV file path')
        parser.add_argument('--race-start', type=str, default='12:00:00', help='Race start time (HH:MM:SS)')

    def handle(self, *args, **options):
        output_path = options['output']
        race_start_str = options['race_start']
        predictions = Prediction.objects.filter(current=True).order_by('id')
        fieldnames = ['runner', 'laptime', 'fixed', 'start_time', 'end_time']

        # Parse race start time (today's date)
        today = datetime.now().date()
        race_start = datetime.strptime(f"{today} {race_start_str}", "%Y-%m-%d %H:%M:%S")

        current_time = race_start

        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for pred in predictions:
                # Parse laptime as HH:MM:SS
                try:
                    h, m, s = [int(x) for x in pred.laptime.split(":")]
                    lap_delta = timedelta(hours=h, minutes=m, seconds=s)
                except Exception:
                    lap_delta = timedelta(0)
                start_time_str = current_time.strftime("%H:%M:%S")
                end_time = current_time + lap_delta
                end_time_str = end_time.strftime("%H:%M:%S")
                writer.writerow({
                    'runner': pred.runner,
                    'laptime': pred.laptime,
                    'start_time': start_time_str,
                    'end_time': end_time_str,
                })
                current_time = end_time

        self.stdout.write(self.style.SUCCESS(f'Exported {predictions.count()} predictions to {output_path}'))