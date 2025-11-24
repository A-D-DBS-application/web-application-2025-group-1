[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DxqGQVx4)

## Local setup

1. Maak een `.env` bestand in de projectroot met minimaal:
   ```
   SECRET_KEY=iets_unieks
   DATABASE_URL=postgresql://postgres:Group1_ADDBS!@jouw-supabase-host.supabase.co:5432/postgres?sslmode=require
   ```
   Tip: open Supabase → Project Settings → Database → Connection String en kopieer de volledige URL (hostnaam, gebruikersnaam, wachtwoord).
2. Installeer dependencies: `python -m pip install -r requirements.txt`.
3. Start de app: `flask --app run.py run` of `python run.py`.

### Problemen oplossen

- Krijg je `sqlalchemy.exc.OperationalError` met “could not translate host name”? Controleer de `DATABASE_URL`: meestal staat er een typefout in de hostnaam.
- Voor lokaal testen zonder externe database kun je de regel `DATABASE_URL=sqlite:///app.db` gebruiken. Migreer daarna met `flask db upgrade`.