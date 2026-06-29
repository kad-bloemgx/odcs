Setup: PostgreSQL + PostgREST + Swagger UI

Dit project bevat een kant-en-klare Docker Compose opzet die:
- een PostgreSQL database start en het DDL `ddl-generator/personen.sql` uitvoert tijdens initialisatie
- een PostgREST service start die automatisch een REST API (en OpenAPI-specificatie) genereert op basis van de database
- een Swagger UI instance start die de PostgREST OpenAPI-specificatie laadt



Bestanden toegevoegd:
- `docker-compose.yml` - compose file voor db, postgrest en swagger
- `ddl-generator/postgrest.conf` - configuratie voor PostgREST
- `ddl-generator/personen.sql` - DDL + voorbeelddata (bestaat al)

Snel starten (vereist Docker & Docker Compose):

```bash
cd /home/gerardb/IdeaProjects/kadaster/dhub/odcs
docker compose up -d
```

Toegang:
- Swagger UI: http://localhost:8080  (laadt OpenAPI spec van PostgREST)
- PostgREST API (raw): http://localhost:3000
- Postgres (host:port): localhost:5432 (user: postgres, password: postgres)

Database roles:
- Superuser: user `postgres` / password `postgres` (used to initialize DB)
- PostgREST anon role: `postgrest` / password `postgrest` (created automatically by init SQL)

Opmerkingen / beveiliging:
- Deze setup maakt een dedicated `postgrest` role aan en geeft deze alleen SELECT op de tabel `personen`.
  Dit is eenvoudiger en veiliger dan gebruik van de superuser als anon role, maar nog steeds niet bedoeld voor productie.
  In productie kies je sterke wachtwoorden, beperk je privileges verder en zet je TLS/authenticatie in.
- PostgREST genereert OpenAPI specificatie op basis van database privileges; als je endpoints ontbreken, controleer dan GRANTs en `db-anon-role`.

Troubleshooting:
- Als Swagger UI geen spec kan laden: open http://localhost:3000 in de browser — je zou de OpenAPI JSON of de PostgREST entry moeten zien.
- Als de DB niet klaar is: wacht tot `docker compose logs db` laat zien dat Postgres klaar is; PostgREST wacht via depends_on healthcheck.

Wil je dat ik:
- automatisch een dedicated DB-gebruiker en GRANT statements toevoeg aan `personen.sql` (aanbevolen), of
- de Swagger UI configureer om via CORS/proxy te werken als je van buiten de host wilt verbinden?

