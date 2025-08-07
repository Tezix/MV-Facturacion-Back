#!/bin/bash
set -e

echo "Ejecutando collectstatic..."
python manage.py collectstatic --noinput

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Despliegue completado exitosamente."
