import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "insightedge.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT column_name, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'reports_report';")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
