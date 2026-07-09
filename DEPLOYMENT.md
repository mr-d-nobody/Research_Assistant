# Deployment

Use real production values in `.env` and rotate any secrets that were ever shared outside the server.

Required backend environment:

```env
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=use-a-long-random-secret
DJANGO_ALLOWED_HOSTS=api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://...
OPENAI_API_KEY=...
TAVILY_API_KEY=...
EMAIL_ADDRESS=...
EMAIL_APP_PASSWORD=...
```

Optional hardening:

```env
AUTH_TOKEN_TTL_HOURS=168
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_CSRF_COOKIE_SECURE=true
DJANGO_HSTS_SECONDS=31536000
DJANGO_HSTS_INCLUDE_SUBDOMAINS=true
DJANGO_HSTS_PRELOAD=true
```

Only enable HSTS subdomains/preload when every relevant subdomain is HTTPS-ready.

Backend deploy commands:

```bash
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py check --deploy
gunicorn --chdir backend research_api.wsgi:application
```

Frontend deploy:

```bash
cd frontend
npm ci
npm run build
```

If the frontend and backend are on different domains, set `VITE_API_BASE_URL` for the frontend build.

Create admin/superuser accounts manually with Django. The app no longer auto-promotes any username.
