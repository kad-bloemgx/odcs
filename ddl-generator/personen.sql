-- DDL Generated from Data Contract: Personen v1.0.0
-- Database type: postgresql

CREATE TABLE personen (
    id VARCHAR(255) NOT NULL,
    naam VARCHAR(255) NOT NULL,
    adres_id VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

COMMENT ON COLUMN personen.id IS 'Unieke identificatie van de persoon';
COMMENT ON COLUMN personen.naam IS 'Volledige naam van de persoon';
COMMENT ON COLUMN personen.adres_id IS 'Referentie naar de ADRES entity';

-- Example data
INSERT INTO personen (id, naam, adres_id) VALUES ('123456', 'Jan Jansen', 'ADDR001');
INSERT INTO personen (id, naam, adres_id) VALUES ('123457', 'Maria Pieterse', 'ADDR002');

-- Indexes for performance
CREATE INDEX idx_personen_naam ON personen (naam);
CREATE INDEX idx_personen_adres_id ON personen (adres_id);

CREATE TABLE adressen (
    id VARCHAR(255) NOT NULL,
    straat VARCHAR(255) NOT NULL,
    huisnummer VARCHAR(255) NOT NULL,
    postcode VARCHAR(255) NOT NULL,
    woonplaats VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

COMMENT ON COLUMN adressen.id IS 'Unieke adres ID';
COMMENT ON COLUMN adressen.straat IS 'Straatnaam';
COMMENT ON COLUMN adressen.huisnummer IS 'Huisnummer';
COMMENT ON COLUMN adressen.postcode IS 'Postcode';
COMMENT ON COLUMN adressen.woonplaats IS 'Woonplaats of gemeente';

-- Example data
INSERT INTO adressen (id, straat, huisnummer, postcode, woonplaats) VALUES ('ADDR001', 'Koppejan', '1', '7461 DB', 'Rijssen');
INSERT INTO adressen (id, straat, huisnummer, postcode, woonplaats) VALUES ('ADDR002', 'Kerkweg', '42', '7411 CX', 'Deventer');

-- Indexes for performance
CREATE INDEX idx_adressen_straat ON adressen (straat);
CREATE INDEX idx_adressen_huisnummer ON adressen (huisnummer);
CREATE INDEX idx_adressen_postcode ON adressen (postcode);
CREATE INDEX idx_adressen_woonplaats ON adressen (woonplaats);
