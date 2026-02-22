"""
Django management command for seeding standard Allergen definitions.

This command creates the standard allergen definitions used across E-Menum.
Allergens are platform-level entities (not tenant-specific) and are used
to label products with allergen information for customer safety.

The allergens follow EU allergen labeling regulations (EU FIC 1169/2011)
which require declaration of the 14 major allergens.

Standard Allergens (EU 14):
| Code | Name         | Description                                          |
|------|--------------|------------------------------------------------------|
| GLU  | Gluten       | Cereals containing gluten (wheat, barley, rye, oats) |
| CRU  | Crustaceans  | Shrimp, crab, lobster, crayfish                      |
| EGG  | Eggs         | All egg products                                     |
| FSH  | Fish         | All fish species                                     |
| PNT  | Peanuts      | Peanuts and peanut products                          |
| SOY  | Soy          | Soybeans and soy products                            |
| MLK  | Milk         | All dairy products containing lactose                |
| NUT  | Tree Nuts    | Almonds, hazelnuts, walnuts, cashews, pecans, etc.   |
| CEL  | Celery       | Celery and celeriac                                  |
| MUS  | Mustard      | All mustard products                                 |
| SES  | Sesame       | Sesame seeds and sesame oil                          |
| SUL  | Sulphites    | Sulphur dioxide and sulphites (>10mg/kg or >10mg/L)  |
| LUP  | Lupin        | Lupin seeds and flour                                |
| MOL  | Molluscs     | Oysters, mussels, clams, squid, octopus              |

Usage:
    python manage.py seed_allergens
    python manage.py seed_allergens --force  # Force update existing records
    python manage.py seed_allergens --dry-run  # Show what would be created
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.menu.models import Allergen


class Command(BaseCommand):
    """Management command to seed standard allergen definitions."""

    help = 'Seed standard allergen definitions for E-Menum (EU 14 allergens)'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing records',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        force = options['force']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        try:
            with transaction.atomic():
                # Create allergens
                allergens = self._create_allergens(force, dry_run)
                self.stdout.write(f'Created/updated {len(allergens)} allergens')

                if dry_run:
                    # Rollback in dry run
                    raise DryRunException()

        except DryRunException:
            self.stdout.write(self.style.WARNING('Dry run completed - no changes were made'))
        except Exception as e:
            raise CommandError(f'Failed to seed allergens: {str(e)}')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Successfully seeded allergens!'))

    def _create_allergens(self, force: bool, dry_run: bool) -> dict:
        """Create or update allergen definitions."""
        # Standard EU 14 allergens as per EU FIC 1169/2011
        allergens_data = [
            {
                'code': 'GLU',
                'name': 'Gluten',
                'slug': 'gluten',
                'description': (
                    'Cereals containing gluten, namely: wheat (such as spelt and khorasan wheat), '
                    'rye, barley, oats or their hybridised strains, and products thereof.'
                ),
                'sort_order': 10,
                'is_active': True,
            },
            {
                'code': 'CRU',
                'name': 'Crustaceans',
                'slug': 'crustaceans',
                'description': (
                    'Crustaceans and products thereof, including shrimp, crab, lobster, '
                    'crayfish, and prawns.'
                ),
                'sort_order': 20,
                'is_active': True,
            },
            {
                'code': 'EGG',
                'name': 'Eggs',
                'slug': 'eggs',
                'description': (
                    'Eggs and products thereof, including whole eggs, egg whites, egg yolks, '
                    'egg powder, and any preparations containing eggs.'
                ),
                'sort_order': 30,
                'is_active': True,
            },
            {
                'code': 'FSH',
                'name': 'Fish',
                'slug': 'fish',
                'description': (
                    'Fish and products thereof, including all fish species, fish sauce, '
                    'fish oil, and products containing fish-derived ingredients.'
                ),
                'sort_order': 40,
                'is_active': True,
            },
            {
                'code': 'PNT',
                'name': 'Peanuts',
                'slug': 'peanuts',
                'description': (
                    'Peanuts and products thereof, including peanut butter, peanut oil, '
                    'and products containing peanut-derived ingredients.'
                ),
                'sort_order': 50,
                'is_active': True,
            },
            {
                'code': 'SOY',
                'name': 'Soy',
                'slug': 'soy',
                'description': (
                    'Soybeans and products thereof, including soy sauce, tofu, soy milk, '
                    'soy lecithin, and products containing soy-derived ingredients.'
                ),
                'sort_order': 60,
                'is_active': True,
            },
            {
                'code': 'MLK',
                'name': 'Milk',
                'slug': 'milk',
                'description': (
                    'Milk and products thereof, including lactose, butter, cheese, cream, '
                    'yogurt, and any preparations containing milk proteins.'
                ),
                'sort_order': 70,
                'is_active': True,
            },
            {
                'code': 'NUT',
                'name': 'Tree Nuts',
                'slug': 'tree-nuts',
                'description': (
                    'Tree nuts: almonds, hazelnuts, walnuts, cashews, pecans, Brazil nuts, '
                    'pistachios, macadamia nuts, and products thereof.'
                ),
                'sort_order': 80,
                'is_active': True,
            },
            {
                'code': 'CEL',
                'name': 'Celery',
                'slug': 'celery',
                'description': (
                    'Celery and products thereof, including celery stalks, leaves, seeds, '
                    'celeriac (celery root), and celery salt.'
                ),
                'sort_order': 90,
                'is_active': True,
            },
            {
                'code': 'MUS',
                'name': 'Mustard',
                'slug': 'mustard',
                'description': (
                    'Mustard and products thereof, including mustard seeds, mustard powder, '
                    'prepared mustard, and mustard oil.'
                ),
                'sort_order': 100,
                'is_active': True,
            },
            {
                'code': 'SES',
                'name': 'Sesame',
                'slug': 'sesame',
                'description': (
                    'Sesame seeds and products thereof, including sesame oil, tahini, '
                    'halva, and products containing sesame-derived ingredients.'
                ),
                'sort_order': 110,
                'is_active': True,
            },
            {
                'code': 'SUL',
                'name': 'Sulphites',
                'slug': 'sulphites',
                'description': (
                    'Sulphur dioxide and sulphites at concentrations of more than '
                    '10 mg/kg or 10 mg/litre expressed as SO2. Common in wine, dried fruits, '
                    'and processed foods.'
                ),
                'sort_order': 120,
                'is_active': True,
            },
            {
                'code': 'LUP',
                'name': 'Lupin',
                'slug': 'lupin',
                'description': (
                    'Lupin and products thereof, including lupin seeds, lupin flour, '
                    'and products containing lupin-derived ingredients. Often found in '
                    'gluten-free alternatives.'
                ),
                'sort_order': 130,
                'is_active': True,
            },
            {
                'code': 'MOL',
                'name': 'Molluscs',
                'slug': 'molluscs',
                'description': (
                    'Molluscs and products thereof, including oysters, mussels, clams, '
                    'scallops, squid, octopus, and snails.'
                ),
                'sort_order': 140,
                'is_active': True,
            },
        ]

        created_allergens = {}
        for data in allergens_data:
            code = data['code']
            slug = data['slug']

            # Check by both code and slug for uniqueness
            existing_by_code = Allergen.objects.filter(code=code).first()
            existing_by_slug = Allergen.objects.filter(slug=slug).first()

            if existing_by_code or existing_by_slug:
                existing = existing_by_code or existing_by_slug
                if force:
                    # Update existing record
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.save()
                    self.stdout.write(f'  ~ Updated allergen: {data["name"]} ({code})')
                else:
                    self.stdout.write(
                        f'  - Skipped allergen: {data["name"]} ({code}) (already exists)'
                    )
                created_allergens[code] = existing
            else:
                # Create new record
                allergen = Allergen.objects.create(**data)
                self.stdout.write(f'  + Created allergen: {data["name"]} ({code})')
                created_allergens[code] = allergen

        return created_allergens


class DryRunException(Exception):
    """Exception raised to rollback dry run transactions."""
    pass
