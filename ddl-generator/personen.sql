-- DDL Generated from Data Contract: Personen v1.0.0
-- Database type: postgresql

-- Create a dedicated DB role for PostgREST (used as anon role)
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'postgrest') THEN
      CREATE ROLE postgrest LOGIN PASSWORD 'postgrest';
   END IF;
END
$$;

-- Ensure the role can connect to the database
GRANT CONNECT ON DATABASE postgres TO postgrest;

CREATE TABLE personen (
    id VARCHAR(255) NOT NULL,
    naam VARCHAR(255) NOT NULL,
    adres VARCHAR(255) NOT NULL,
    woonplaats VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

-- Column comments (PostgreSQL uses COMMENT ON COLUMN)
COMMENT ON COLUMN personen.id IS 'Unieke identificatie van de persoon';
COMMENT ON COLUMN personen.naam IS 'Volledige naam van de persoon';
COMMENT ON COLUMN personen.adres IS 'Volledig adres (straat en huisnummer)';
COMMENT ON COLUMN personen.woonplaats IS 'Woonplaats of gemeente';

-- Make schema/table visible to the postgrest role and grant select
GRANT USAGE ON SCHEMA public TO postgrest;
GRANT SELECT ON TABLE personen TO postgrest;

-- Example data
INSERT INTO personen (id, naam, adres, woonplaats) VALUES ('123456', 'Jan Jansen', 'Koppejan 1, 7461 DB', 'Rijssen');
INSERT INTO personen (id, naam, adres, woonplaats) VALUES ('123457', 'Maria Pieterse', 'Kerkweg 42, 7411 CX', 'Deventer');

-- Indexes for performance
CREATE INDEX idx_personen_naam ON personen (naam);
CREATE INDEX idx_personen_adres ON personen (adres);
CREATE INDEX idx_personen_woonplaats ON personen (woonplaats);

-- Provinces table and example (Gelderland) import
CREATE TABLE IF NOT EXISTS provincies (
    id VARCHAR(255) PRIMARY KEY,
    properties JSONB,
    geom geometry(Geometry,4326)
);

-- Insert simplified Gelderland polygon (WGS84)
INSERT INTO provincies (id, properties, geom) VALUES (
  'gelderland',
  '{"name":"Gelderland","source":"approximate-generated","note":"Approximate demo polygon in WGS84 (lat/lon). Use official boundaries for production.","code":"PV31","description":"Limburg","value":"95,1","unit":"%"}'::jsonb,
  ST_SetSRID(ST_GeomFromGeoJSON('{"type":"Polygon","coordinates":[[[6.0500,51.7600],[6.1500,51.8200],[6.2500,51.8600],[6.3600,51.9300],[6.4300,52.0100],[6.5200,52.0800],[6.6400,52.1500],[6.8200,52.2000],[7.0000,52.1800],[7.0600,52.1200],[6.9800,52.0600],[6.9200,51.9800],[6.8200,51.9300],[6.7000,51.8800],[6.6000,51.8200],[6.4800,51.7800],[6.3000,51.7400],[6.1800,51.7200],[6.0900,51.7400],[6.0500,51.7600]]]}'),4326)
);

-- Create a view exposing properties and geometry as GeoJSON
CREATE OR REPLACE VIEW provincies_view AS
  SELECT id,
         properties,
         ST_AsGeoJSON(geom)::jsonb AS geometry
  FROM provincies;

GRANT SELECT ON TABLE provincies TO postgrest;
GRANT SELECT ON TABLE provincies_view TO postgrest;

