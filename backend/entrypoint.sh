#!/bin/bash
set -e

MAX_RETRIES=30
PROCESS_TYPE=${PROCESS_TYPE:-web}

if [ -n "$DATABASE_URL" ]; then
    echo "⏳ Attente de PostgreSQL..."
    retries=0
    while ! python -c "
import os, psycopg2
psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=2).close()
" 2>/dev/null; do
        retries=$((retries + 1))
        if [ $retries -ge $MAX_RETRIES ]; then
            echo "❌ PostgreSQL injoignable après ${MAX_RETRIES} tentatives"
            exit 1
        fi
        sleep 2
    done
    echo "✅ PostgreSQL prêt"
fi

if [ -n "$REDIS_URL" ]; then
    echo "⏳ Attente de Redis..."
    retries=0
    while ! python -c "
import os, redis
redis.from_url(os.environ['REDIS_URL'], socket_connect_timeout=2).ping()
" 2>/dev/null; do
        retries=$((retries + 1))
        if [ $retries -ge $MAX_RETRIES ]; then
            echo "❌ Redis injoignable après ${MAX_RETRIES} tentatives"
            exit 1
        fi
        sleep 2
    done
    echo "✅ Redis prêt"
fi

case "$PROCESS_TYPE" in
    celery-worker)
        echo "🚀 Démarrage Celery Worker"
        exec celery -A config worker -l info --concurrency=2 --hostname=worker1@%h
        ;;
    celery-beat)
        echo "🚀 Démarrage Celery Beat"
        exec celery -A config beat -l info
        ;;
    *)
        echo "⏳ Migrations..."
        python manage.py migrate --noinput
        echo "⏳ Collectstatic..."
        python manage.py collectstatic --noinput
        echo "🚀 Démarrage Daphne sur 0.0.0.0:8000"
        exec daphne -b 0.0.0.0 -p 8000 --proxy-headers config.asgi:application
        ;;
esac
