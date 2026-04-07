# monajent
Mon Ajent MVP

# ### JETON CLOUDFLARE ####
## Pour vous authentifier auprès de l’API Cloudflare Utilisez votre jeton :

Valeur du jeton:
```
rjEPTZa********
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
## BUILD PROD (Dokploy / images Docker)

À lancer **depuis le dossier `monajent/`** (là où se trouvent `docker-compose.build.yml` et le `.env` lu par Compose).

```bash
export VITE_API_BASE_URL=https://api.monajent.com
export VITE_PAYSTACK_PUBLIC_KEY=pk_live_26c2d6a1d9a134672175eec45142fca68e7052f9   # clé publique Paystack (dashboard)

docker buildx bake -f docker-compose.build.yml \
  --builder cloud-ciacems-ciacems-builder \
  --push
```

Ne **pas** mettre de scripts shell (`curl`, blocs multi-lignes) dans le fichier **`.env`** : voir explication ci-dessous. Tests API externes (ex. Gemini) : script à part ou variables `KEY=value` uniquement.

`SECRET_KEY` Django (Dokploy / serveur, ne pas commiter) :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## CHARTE GRAPHIQUE
