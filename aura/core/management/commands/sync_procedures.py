from django.core.management.base import BaseCommand
from django.conf import settings
import snowflake.connector
import json
from core.models import Procedure

class Command(BaseCommand):
    help = 'Syncs procedures from the master Snowflake database to the local SQLite cache.'

    def handle(self, *args, **options):
        self.stdout.write("Starting procedure sync from Snowflake...")

        try:
            # We will need to add SNOWFLAKE creds to settings.py
            # or read them from a .env file here.
            conn = snowflake.connector.connect(
                user=settings.SNOWFLAKE_USER,
                password=settings.SNOWFLAKE_PASSWORD,
                account=settings.SNOWFLAKE_ACCOUNT,
                # ... etc ...
            )
            
            with conn.cursor() as cur:
                cur.execute("SELECT procedure_id, component_name, steps, safety_warnings FROM PROCEDURES")
                for row in cur:
                    procedure_id, component_name, steps_json, warnings_json = row
                    
                    # Use update_or_create to insert or update local records
                    obj, created = Procedure.objects.update_or_create(
                        procedure_id=procedure_id,
                        defaults={
                            'component_name': component_name,
                            'steps': json.loads(steps_json),
                            'safety_warnings': json.loads(warnings_json)
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created new procedure: {procedure_id}"))
                    else:
                        self.stdout.write(f"Updated existing procedure: {procedure_id}")

            conn.close()
            self.stdout.write(self.style.SUCCESS("Sync completed successfully!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Sync failed: {e}"))