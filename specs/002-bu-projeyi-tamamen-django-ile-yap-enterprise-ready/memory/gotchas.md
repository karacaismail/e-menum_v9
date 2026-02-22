# Gotchas & Pitfalls

Things to watch out for in this codebase.

## [2026-02-14 10:27]
Python commands (python, python3, pip) are not in the allowed commands list. The verification commands for Django project setup require python to be added to the security configuration.

_Context: Implementing subtask-1-1: Django project skeleton creation. The verification command 'python manage.py check' cannot run until Python is added to allowed commands in .auto-claude-security.json_

## [2026-02-14 10:36]
Python commands (python/python3) are blocked in this project - cannot run Django verification commands directly

_Context: Attempted to verify settings with DJANGO_SETTINGS_MODULE=config.settings.development python -c command_

## [2026-02-14 10:53]
Python commands (python, python3) are blocked in this project environment. Verification commands that require Python cannot be executed directly.

_Context: When trying to verify Django models with python -c command_

## [2026-02-14 10:54]
Organization.plan ForeignKey references 'subscriptions.Plan' which doesn't exist yet. This is a lazy reference that Django will resolve when subscriptions app is created. Migrations should be created after subscriptions.Plan exists.

_Context: Creating Organization model before subscriptions app exists_

## [2026-02-14 11:05]
Organization.plan FK must be added AFTER subscriptions app is created. The FK is commented out in models.py and excluded from 0001_initial migration. A migration 0002_add_organization_plan.py should be created after subtask-6-* (subscriptions models) is complete.

_Context: Creating core migrations while subscriptions.Plan model doesn't exist yet. Django lazy references work but migrations would fail to apply without the target model._

## [2026-02-14 12:18]
Python commands (python, python3) are blocked in this environment. To generate Django migrations, manually write the migration file based on the models.py file, following the pattern from existing migrations (e.g., menu/migrations/0001_initial.py).

_Context: Encountered during subtask-5-6 when trying to run makemigrations. Solution: manually create migrations/0001_initial.py following existing patterns._

## [2026-02-14 13:40]
drf-nested-routers package added to requirements.txt for nested URL routing (products/{id}/variants/, products/{id}/modifiers/). Import as `from rest_framework_nested import routers`.

_Context: When creating nested REST API routes for related resources like product variants and modifiers._

## [2026-02-14 14:50]
Python commands blocked - cannot run verification commands like 'python -c'. Manual verification of factories requires external testing environment.

_Context: During subtask-12-2, verification command for factories could not be executed due to Python being blocked. Files were created following factory-boy patterns._
