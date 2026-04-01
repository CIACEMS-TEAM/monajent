# monajent
Mon Ajent MVP

# ### JETON CLOUDFLARE ####
## Utilisez ce jeton pour vous authentifier auprès de l’API Cloudflare :

Valeur du jeton:
```
rjEPTZafprJmLhaoCW1ROiUKjp-DPPHNoLndenGs
```


## CHARTE GRAPHIQUE 


###  COMMANDE DE DEPLOIEMENT LOCAL ET BUILD PROD 

## LOCAL ###

```
Workflow dev local

# Mode léger (SQLite + LocMemCache) — rien à lancer
cd backend && source venv/bin/activate && python manage.py runserver

# Mode complet (PostgreSQL + Redis) — décommenter dans .env puis :
docker compose up -d
cd backend && source venv/bin/activate && python manage.py runserver

```
## BUILD PROD ###
# Workflow production (Dokploy)


```
# Build
VITE_API_BASE_URL=https://api.monajent.com \
    VITE_PAYSTACK_PUBLIC_KEY=pk_live_26c2d6a1d9a134672175eec45142fca68e7052f9 \
      docker buildx bake -f docker-compose.build.yml \
        --builder cloud-ciacems-ciacems-builder --push

# Deploy → Dokploy tire l'image et injecte les variables via son UI

```

SECRET_KEY=<générer avec python3 -c "import secrets;print(secrets.token_urlsafe(50))">
