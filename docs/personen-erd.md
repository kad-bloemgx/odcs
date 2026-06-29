# Entity Relationship Diagram - Personen

## Entiteiten

### Personentabel
| Veld | Type | Omschrijving | Relatie |
|------|------|--------------|---------|
| id | string | Unieke identificatie van de persoon | Primary Key |
| naam | string | Volledige naam van de persoon |  |
| adres_id | string | Referentie naar de ADRES entity | Foreign Key → adressen.id |

### Adrestabel
| Veld | Type | Omschrijving | Relatie |
|------|------|--------------|---------|
| id | string | Unieke adres ID | Primary Key |
| straat | string | Straatnaam |  |
| huisnummer | string | Huisnummer |  |
| postcode | string | Postcode |  |
| woonplaats | string | Woonplaats of gemeente |  |
| personen | array | Personen die op dit adres wonen | Inverse Foreign Key ← personen.adres_id |

## Relaties
- **Personen** → **Adressen**: Een persoon heeft één adres (1:N relatie)
- **Adressen** ← **Personen**: Een adres kan meerdere personen bevatten

## SLA Specificaties
- Beschikbaarheid: 99.5% maandelijks
- Actualiteit: Maximaal 24 uur oud
- Response tijd p99: maximaal 500ms

## Voorbeeldgegevens

### Personen
| id | naam | adres_id |
|----|------|----------|
| 123456 | Jan Jansen | ADDR001 |
| 123458 | Pietje Puk | ADDR001 |
| 123457 | Maria Pieterse | ADDR002 |

### Adressen
| id | straat | huisnummer | postcode | woonplaats |
|----|--------|------------|----------|------------|
| ADDR001 | Koppejan | 1 | 7461 DB | Rijssen |
| ADDR002 | Kerkweg | 42 | 7411 CX | Deventer |

## Technische Specificaties
- Ondersteunde formaten: JSON, CSV, Parquet
- API endpoints: https://api.kadaster.nl/v1
- Development endpoint: https://api-dev.kadaster.nl/v1