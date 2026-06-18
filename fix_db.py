import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "insightedge.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("ALTER TABLE reports_report DROP COLUMN IF EXISTS incident_date CASCADE;")
    cursor.execute("ALTER TABLE reports_report DROP COLUMN IF EXISTS risk_level CASCADE;")
    cursor.execute("ALTER TABLE reports_report DROP COLUMN IF EXISTS behavior_category CASCADE;")
    
print("Dropped leftover columns from previous branch.")
