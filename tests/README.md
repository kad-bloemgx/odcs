# ODCS API Testen

Deze directory bevat testplannen voor het valideren van de gegenereerde API's (REST en GraphQL).

## JMeter Testplan

Het bestand `api-test.jmx` is een Apache JMeter testplan dat zowel de PostgREST service (poort 3000) als de PostGraphile service (poort 5000) befragt.

### Vereisten
- Apache JMeter geïnstalleerd.
- De Docker containers moeten draaien (`docker compose up -d`).

### Uitvoeren via de GUI
1. Start JMeter.
2. Open `tests/api-test.jmx`.
3. Klik op de groene startknop.
4. Bekijk de resultaten in "View Results Tree" of "Summary Report".

### Uitvoeren via de Command Line (CLI)
```bash
jmeter -n -t tests/api-test.jmx -l tests/results.jtl
```

### Wat wordt getest?
1. **REST API**: Een GET request naar `/adressen?select=*,personen(*)` om te controleren of adressen en geneste personen correct worden teruggegeven.
2. **GraphQL API**: Een POST query naar `/graphql` die adressen en hun gerelateerde personen ophaalt via het GraphQL schema.
