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
export VITE_POSTHOG_PROJECT_TOKEN=phc_mNWy6S4UE7EszTjASNhbqpiYNJFLx4ZRf4foFW4uKmyS
export VITE_POSTHOG_HOST=https://us.i.posthog.com

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






#### MOBILE RESOLUTIONS #######

Smartphones (Téléphones)
iPhone SE : 375 x 667 px
iPhone XR : 414 x 896 px
iPhone 12 Pro : 390 x 844 px
iPhone 14 Pro Max : 430 x 932 px
Pixel 7 : 412 x 915 px
Samsung Galaxy S8+ : 360 x 740 px
Samsung Galaxy S20 Ultra : 412 x 915 px
Samsung Galaxy A51/71 : 412 x 914 px
Tablettes et Pliables
iPad Mini : 768 x 1024 px
iPad Air : 820 x 1180 px
iPad Pro : 1024 x 1366 px
Surface Pro 7 : 912 x 1368 px
Surface Duo : 540 x 720 px (un seul écran)
Galaxy Z Fold 5 : 344 x 882 px (écran plié) / 673 x 796 px (écran déplié)
Asus Zenbook Fold : 853 x 1280 px (plié) / 1280 x 1707 px (déplié)
Écrans Connectés (Smart Displays)
Nest Hub : 1024 x 600 px
Nest Hub Max : 1280 x 800 px
Note technique : Ces valeurs correspondent aux "points" (Viewport). Pour obtenir la résolution physique réelle, il faut multiplier ces chiffres par le Device Pixel Ratio (DPR) de l'appareil (souvent x2 ou x3 pour les écrans Retina/OLED).