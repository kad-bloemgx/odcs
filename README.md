# Project ODCS (Open Data Contract Standard)

Dit project is gericht op het implementeren en demonstreren van gegevensontsluiting op basis van een gestandaardiseerd datacontract.

## Wat is ODCS?
ODCS staat voor **Open Data Contract Standard**. Het is een standaard (in dit project versie `3.1.0`) die wordt gebruikt om afspraken tussen data-aanbieders en consumenten vast te leggen in een machine-leesbaar formaat (`YAML`). Het bevat:
- **Metadata**: Informatie over eigenaarschap (Kadaster), versiebeheer en contactgegevens.
- **Schema**: De technische structuur van de data (zoals de entiteiten `personen` en `adressen`).
- **SLA**: Afspraken over beschikbaarheid (bijv. 99,5%) en hoe actueel de data is.

## Kernonderdelen in dit Project
Het project gebruikt het datacontract (`datacontract/personen.yaml`) als "single source of truth" om verschillende onderdelen automatisch te genereren:
- **Database (SQL/DDL)**: Via een generator (`ddl-generator/`) wordt automatisch de SQL-code aangemaakt om tabellen en indexen in een PostgreSQL-database aan te maken die precies passen bij het contract.
- **API (OpenAPI)**: Er wordt een OpenAPI-specificatie gegenereerd (`openapi/generated-openapi-spec.yaml`) voor de ontsluiting van de data.
- **Documentatie**: Er worden ER-diagrammen (`personen-erd.md`) en analyses gegenereerd die de structuur inzichtelijk maken.

## Technische Stack
- **PostgreSQL**: De database waarin de personen- en adresgegevens worden opgeslagen.
- **PostgREST**: Een tool die de PostgreSQL-database direct omzet in een RESTful API.
- **Swagger UI**: Wordt gebruikt om de gegenereerde API te documenteren en te testen.
- **Docker & Kubernetes (Helm)**: Voor het eenvoudig uitrollen van de volledige stack (Database + API + UI) in verschillende omgevingen.

## Doel van het Project
Het hoofddoel is om te laten zien hoe een **contract-first** benadering zorgt voor consistentie. Wanneer het datacontract wijzigt, kunnen de database, de API-specificatie en de documentatie automatisch worden bijgewerkt, waardoor de kans op fouten en inconsistenties wordt geminimaliseerd.

## Referenties
- [Open Data Contract Standard v3.1.0](https://bitol-io.github.io/open-data-contract-standard/v3.1.0/)
- [PostgREST Documentation](https://docs.postgrest.org/en/v14/)

