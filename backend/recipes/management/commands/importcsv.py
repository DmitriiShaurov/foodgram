import csv
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import ingredients from CSV file'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        settings.BASE_DIR
                    )
                )
            )
        )
        csv_file = os.path.join(
            base_dir,
            'data',
            'ingredients.csv'
        )

        self.stdout.write(
            f'Importing from {csv_file}'
        )

        try:
            with open(csv_file, encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 2:
                        name, measurement_unit = row[0], row[1]
                        Ingredient.objects.get_or_create(
                            name=name,
                            measurement_unit=measurement_unit
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    'Ingredients imported successfully'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error importing ingredients: {e}'
                )
            )
