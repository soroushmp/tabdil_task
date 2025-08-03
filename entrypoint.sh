#!/bin/bash

set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.1
done
echo "PostgreSQL is up and running!"

echo "making database migrations..."
python manage.py makemigrations

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if not exists
echo "Creating superuser if not exists..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
EOF

## Start Gunicorn
echo "Starting Gunicorn..."
#exec gunicorn --bind 0.0.0.0:8000 Tabdil.wsgi:application
exec gunicorn --bind 0.0.0.0:8000 --workers 4 --worker-class=gevent Tabdil.wsgi:application