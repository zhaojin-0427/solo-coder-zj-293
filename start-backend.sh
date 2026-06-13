#!/bin/bash
cd "$(dirname "$0")/backend"

echo "Activating virtual environment..."
source venv/bin/activate

echo "Running database migrations..."
python manage.py migrate

echo "Starting Django server on port 9102..."
python manage.py runserver 0.0.0.0:9102
