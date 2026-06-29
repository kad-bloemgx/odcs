#!/usr/bin/env python3
"""
ODCS Contract to DDL Generator

Zet een Open Data Contract (YAML/JSON) automatisch om naar SQL DDL statements.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

class ContractToDDL:
    # Mapping van JSON Schema types naar SQL types
    TYPE_MAPPING = {
        'string': 'VARCHAR(255)',
        'integer': 'INT',
        'number': 'DECIMAL(10,2)',
        'boolean': 'BOOLEAN',
        'date': 'DATE',
        'date-time': 'TIMESTAMP',
        'object': 'JSON',
        'array': 'JSON'
    }

    def __init__(self, contract_path: str, db_type: str = 'postgresql'):
        """
        Laad contract van YAML of JSON

        Args:
            contract_path: Path naar het contract bestand
            db_type: Database type (postgresql, mysql, sqlite, mssql)
        """
        self.contract = self._load_contract(contract_path)
        self.db_type = db_type.lower()
        self.ddl_statements = []

    def _load_contract(self, path: str) -> Dict[str, Any]:
        """Laad contract YAML/JSON"""
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                try:
                    import yaml
                    return yaml.safe_load(f)
                except ImportError:
                    print("⚠️  Waarschuwing: PyYAML niet gevonden. Gebruik fallback parser voor eenvoudige YAML.")
                    return self._fallback_yaml_load(f.read())
            return json.load(f)

    def _fallback_yaml_load(self, content: str) -> Dict[str, Any]:
        """Eenvoudige fallback voor YAML parsing zonder externe dependencies"""
        result = {}
        lines = content.split('\n')
        stack = [(result, -1)]
        
        # Voor de specifieke structuur van personen.yaml:
        # We hoeven alleen de top-level keys en hun directe objecten/lijsten te vangen
        # Dit is GEEN volledige YAML parser.
        
        current_obj = result
        current_indent = -1
        
        import re
        
        for line in lines:
            if not line.strip() or line.strip().startswith('#'):
                continue
                
            indent = len(line) - len(line.lstrip())
            line = line.strip()
            
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Check for list start
                if not value and indent > current_indent:
                    new_obj = {}
                    if isinstance(current_obj, list):
                        current_obj.append(new_obj)
                    else:
                        current_obj[key] = new_obj
                    stack.append((new_obj, indent))
                    current_obj = new_obj
                    current_indent = indent
                elif value:
                    # Strip quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Handle list within object (e.g. keywords)
                    if indent > current_indent:
                        pass # should already be handled by stack
                    
                    while stack and indent <= stack[-1][1]:
                        stack.pop()
                    
                    if stack:
                        current_obj, current_indent = stack[-1]
                    
                    if isinstance(current_obj, list):
                        # Should not happen in this simplified version for personen.yaml
                        pass
                    else:
                        current_obj[key] = value
            elif line.startswith('- '):
                # Handle list item
                value = line[2:].strip()
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                while stack and indent < stack[-1][1]:
                    stack.pop()
                
                if stack:
                    current_obj, current_indent = stack[-1]
                
                if isinstance(current_obj, list):
                    current_obj.append(value)
                else:
                    # If it's a dict but we see a list item, maybe the previous key should have been a list
                    pass
                pass

        # Gezien de complexiteit van een echte parser, laten we voor deze specifieke taak 
        # een meer doelgerichte aanpak gebruiken als PyYAML ontbreekt.
        return self._doelgerichte_parser(content)

    def _doelgerichte_parser(self, content: str) -> Dict[str, Any]:
        """Heel specifieke parser voor personen.yaml structuur"""
        import re
        result = {}
        
        # Simpele regex voor top-level velden
        for match in re.finditer(r'^(\w+):\s*(.*)$', content, re.MULTILINE):
            key, val = match.groups()
            if val.strip():
                result[key] = val.strip().strip('"').strip("'")

        # Zoek naar schema secties
        def extract_object(section_name, text):
            pattern = rf'^{section_name}:\s*$\n((?:[ ]+.*\n?)*)'
            match = re.search(pattern, text, re.MULTILINE)
            if not match: return {}
            
            obj = {}
            props = {}
            section_text = match.group(1)
            
            # Zoek properties
            prop_match = re.search(r'^[ ]+properties:\s*$\n((?:[ ]{4,}.*\n?)*)', section_text, re.MULTILINE)
            if prop_match:
                prop_text = prop_match.group(1)
                # Extraheer individuele properties
                # We splitsen de prop_text in blokken per property op niveau 4 spaties
                prop_blocks = re.split(r'^[ ]{4}(\w+):\s*$\n?', prop_text, flags=re.MULTILINE)
                # prop_blocks[0] is vaak leeg of bevat alleen witruimte
                for i in range(1, len(prop_blocks), 2):
                    p_name = prop_blocks[i].strip()
                    p_data = prop_blocks[i+1]
                    p_obj = {}
                    
                    # Extract attributes like type, description (niveau 6 spaties)
                    for p_attr in re.finditer(r'^[ ]{6}(\w+):\s*(.*)$', p_data, re.MULTILINE):
                        attr_k, attr_v = p_attr.groups()
                        p_obj[attr_k] = attr_v.strip().strip('"').strip("'")
                    
                    # Extract relationships (niveau 6 spaties)
                    if 'relationships:' in p_data:
                        rels = []
                        # relationships: op niveau 6
                        rel_section_match = re.search(r'^[ ]{6}relationships:\s*$\n((?:[ ]{8,}.*\n?)*)', p_data, re.MULTILINE)
                        if rel_section_match:
                            rel_section = rel_section_match.group(1)
                            # items in lijst op niveau 8
                            # Gebruik een meer robuuste splitsing die ook rekening houdt met meerdere attributen per item
                            rel_items = re.split(r'^[ ]{8}- ', rel_section, flags=re.MULTILINE)
                            for item_text in rel_items:
                                item_text = item_text.strip()
                                if not item_text: continue
                                r_obj = {}
                                # attributen binnen het item
                                for r_attr in re.finditer(r'^[ ]*(\w+):\s*(.*)$', item_text, re.MULTILINE):
                                    ak, av = r_attr.groups()
                                    r_obj[ak] = av.strip().strip('"').strip("'")
                                if r_obj: rels.append(r_obj)
                        p_obj['relationships'] = rels
                        
                    props[p_name] = p_obj
            
            obj['properties'] = props
            
            # Zoek required
            req_match = re.search(r'^[ ]+required:\s*$\n((?:[ ]{4,}- .*\n?)*)', section_text, re.MULTILINE)
            if req_match:
                req_text = req_match.group(1)
                obj['required'] = [r.strip('- ').strip() for r in req_text.strip().split('\n')]
                
            return obj

        result['schema'] = extract_object('schema', content)
        result['adresSchema'] = extract_object('adresSchema', content)
        
        # Voorbeelden extraheren
        examples = {}
        ex_match = re.search(r'^examples:\s*$\n((?:[ ]+.*\n?)*)', content, re.MULTILINE)
        if ex_match:
            ex_text = ex_match.group(1)
            # Voor elke tabel in examples
            for t_match in re.finditer(r'^[ ]{2}(\w+):\s*$\n((?:[ ]{4,}.*\n?)*)', ex_text, re.MULTILINE):
                t_name, t_data = t_match.groups()
                t_list = []
                # Voor elk record (begint met - id:)
                records = re.split(r'^[ ]{4}- ', t_data, flags=re.MULTILINE)
                for rec in records[1:]: # eerste is leeg
                    rec_obj = {}
                    # Gebruik een betere regex voor attributes die rekening houdt met inspringen
                    # Match key: value, waarbij value ook optionele spaties aan het begin kan hebben
                    for r_attr in re.finditer(r'^[ ]*(\w+):\s*(.*)$', rec, re.MULTILINE):
                        r_k, r_v = r_attr.groups()
                        rec_obj[r_k] = r_v.strip().strip('"').strip("'")
                    t_list.append(rec_obj)
                examples[t_name] = t_list
        result['examples'] = examples
        
        return result

    def _get_sql_type(self, json_type: str, format_spec: str = None) -> str:
        """
        Bepaal SQL type op basis van JSON Schema type

        Args:
            json_type: JSON Schema type
            format_spec: Format specifier (e.g., 'date', 'email', 'uri')
        """
        # Check op format specifier
        if format_spec:
            if format_spec == 'email':
                return 'VARCHAR(255)'
            elif format_spec == 'date':
                return 'DATE'
            elif format_spec == 'date-time':
                return 'TIMESTAMP'
            elif format_spec == 'uri':
                return 'TEXT'

        # Fallback op basis van type
        base_type = self.TYPE_MAPPING.get(json_type, 'VARCHAR(255)')

        # Prefer JSONB for PostgreSQL
        if json_type in ['object', 'array'] and self.db_type == 'postgresql':
            return 'JSONB'

        return base_type

    def generate_create_table(self, table_name: str = None, schema_data: Dict = None) -> (str, List[str]):
        """
        Genereer CREATE TABLE statement

        Args:
            table_name: Tabel naam (standaard uit contract id)
            schema_data: Schema data dict (standaard uit contract schema)
        """
        if not table_name:
            table_name = self.contract.get('id', 'data').replace('-', '_')

        if not schema_data:
            schema_data = self.contract.get('schema', {})

        properties = schema_data.get('properties', {})
        required_fields = schema_data.get('required', [])

        if not properties:
            raise ValueError("Contract bevat geen schema.properties")

        # Start CREATE TABLE
        sql = f"CREATE TABLE {table_name} (\n"

        columns = []
        column_comments: List[str] = []
        for field_name, field_spec in properties.items():
            # Sla virtuele/inverse relaties over voor de fysieke tabel definitie
            relationships = field_spec.get('relationships', [])
            is_virtual = any(rel.get('type') == 'inverseForeignKey' for rel in relationships if isinstance(rel, dict))
            if is_virtual:
                continue

            # Bepaal SQL type
            field_type = field_spec.get('type', 'string')
            field_format = field_spec.get('format')
            sql_type = self._get_sql_type(field_type, field_format)

            # Build kolom definition
            column_def = f"    {field_name} {sql_type}"

            # Add NOT NULL voor required fields
            if field_name in required_fields:
                column_def += " NOT NULL"

            # Add description as comment: for MySQL we can keep inline COMMENT,
            # for PostgreSQL we must add a separate COMMENT ON COLUMN statement.
            description = field_spec.get('description', '')
            if description and self.db_type not in ['sqlite']:
                safe_desc = description.replace("'", "''")
                if self.db_type == 'mysql':
                    column_def += f" COMMENT '{safe_desc}'"
                elif self.db_type == 'postgresql':
                    # collect comment statements to add after CREATE TABLE
                    column_comments.append(f"COMMENT ON COLUMN {table_name}.{field_name} IS '{safe_desc}';")
                else:
                    # default: attach as inline comment when supported
                    column_def += f" COMMENT '{safe_desc}'"

            columns.append(column_def)

        # Primary key (standaard eerste id veld)
        if 'id' in properties:
            columns.append("    PRIMARY KEY (id)")
        elif required_fields:
            pk_field = required_fields[0]
            columns.append(f"    PRIMARY KEY ({pk_field})")

        sql += ",\n".join(columns)
        
        # Add foreign keys if any
        fk_statements = []
        for field_name, field_spec in properties.items():
            relationships = field_spec.get('relationships', [])
            for rel in relationships:
                if isinstance(rel, dict) and rel.get('type') == 'foreignKey' and 'to' in rel:
                    to_ref = rel['to']
                    if '.' in to_ref:
                        ref_table, ref_col = to_ref.split('.', 1)
                        if self.db_type == 'postgresql':
                            fk_statements.append(f"ALTER TABLE {table_name} ADD CONSTRAINT fk_{table_name}_{field_name} FOREIGN KEY ({field_name}) REFERENCES {ref_table} ({ref_col});")
                        else:
                            # Inline for others or also ALTER
                            fk_statements.append(f"ALTER TABLE {table_name} ADD FOREIGN KEY ({field_name}) REFERENCES {ref_table} ({ref_col});")

        sql += "\n);"

        return sql, column_comments, fk_statements

    def generate_insert_examples(self, table_name: str = None, examples_data: List = None, schema_data: Dict = None) -> List[str]:
        """
        Genereer INSERT statements op basis van examples

        Args:
            table_name: Tabel naam (standaard uit contract id)
            examples_data: Lijst van example records
            schema_data: Schema data dict
        """
        if not table_name:
            table_name = self.contract.get('id', 'data').replace('-', '_')

        if not examples_data:
            examples_data = self.contract.get('examples', [])

        if not schema_data:
            schema_data = self.contract.get('schema', {})

        insert_statements = []

        properties = schema_data.get('properties', {})

        # Handle examples lijst of dict format
        examples_list = examples_data if isinstance(examples_data, list) else []

        for example in examples_list:
            columns = []
            values = []

            for col_name in properties.keys():
                if col_name in example:
                    columns.append(col_name)
                    value = example[col_name]
                    # Escape string values
                    if isinstance(value, str):
                        value = value.replace("'", "''")
                        values.append(f"'{value}'")
                    elif isinstance(value, bool):
                        values.append(str(value).lower())
                    else:
                        values.append(str(value))

            col_list = ", ".join(columns)
            val_list = ", ".join(values)
            insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({val_list});"
            insert_statements.append(insert_sql)

        return insert_statements

    def generate_index_statements(self, table_name: str = None, schema_data: Dict = None) -> List[str]:
        """
        Genereer INDEX statements

        Args:
            table_name: Tabel naam (standaard uit contract id)
            schema_data: Schema data dict
        """
        if not table_name:
            table_name = self.contract.get('id', 'data').replace('-', '_')

        if not schema_data:
            schema_data = self.contract.get('schema', {})

        indexes = []
        properties = schema_data.get('properties', {})

        # Maak index op alle non-primary key velden
        for field_name, field_spec in properties.items():
            if field_name != 'id':
                # Sla virtuele/inverse relaties over
                relationships = field_spec.get('relationships', [])
                is_virtual = any(rel.get('type') == 'inverseForeignKey' for rel in relationships if isinstance(rel, dict))
                if is_virtual:
                    continue

                index_name = f"idx_{table_name}_{field_name}"
                indexes.append(f"CREATE INDEX {index_name} ON {table_name} ({field_name});")

        return indexes

    def generate_all_ddl(self, table_name: str = None) -> str:
        """
        Genereer complete DDL (CREATE TABLE + INSERT examples + INDEXES)

        Ondersteunt meerdere tabellen gedefinieerd in het contract:
        - schema → per se table
        - adresSchema, contactSchema, etc. → automatisch gedetecteerd

        Args:
            table_name: Tabel naam (optioneel, standaard uit contract id)
        """
        ddl = []

        # Metadata commentary
        contract_name = self.contract.get('name', 'Data Contract')
        contract_version = self.contract.get('version', '1.0.0')
        ddl.append(f"-- DDL Generated from Data Contract: {contract_name} v{contract_version}")
        ddl.append(f"-- Database type: {self.db_type}")
        ddl.append("")

        # Add PostgREST roles and permissions if database is PostgreSQL
        if self.db_type == 'postgresql':
            ddl.append("-- Create roles if they don't exist")
            ddl.append("DO $$")
            ddl.append("BEGIN")
            ddl.append("    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgrest') THEN")
            ddl.append("        CREATE ROLE postgrest nologin;")
            ddl.append("    END IF;")
            ddl.append("END")
            ddl.append("$$;")
            ddl.append("")
            ddl.append("GRANT usage ON SCHEMA public TO postgrest;")
            ddl.append("GRANT SELECT ON ALL TABLES IN SCHEMA public TO postgrest;")
            ddl.append("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO postgrest;")
            ddl.append("")

        # Collect all schema definitions
        schemas = {}
        examples_dict = self.contract.get('examples', {})

        # Primary schema
        if 'schema' in self.contract:
            base_table_name = table_name if table_name else self.contract.get('id', 'data').replace('-', '_')
            schemas[base_table_name] = self.contract.get('schema')

        # Additional schemas (adresSchema, contactSchema, etc.)
        # Look for keys in examples dict to determine correct table names
        for key, value in self.contract.items():
            if key.endswith('Schema') and key != 'schema' and isinstance(value, dict):
                # Derive schema name and look for matching examples key
                schema_base = key.replace('Schema', '')

                # Try to find matching examples key (e.g., "adressen", "contacten")
                table_name_key = None
                if isinstance(examples_dict, dict):
                    for examples_key in examples_dict.keys():
                        # Match if examples_key contains schema_base (case-insensitive)
                        if schema_base.lower() in examples_key.lower():
                            table_name_key = examples_key
                            break

                # If no match found, apply simple pluralization
                if not table_name_key:
                    # Dutch pluralization rules
                    if schema_base.endswith(('s', 'z')):
                        table_name_key = schema_base + 'sen'
                    elif schema_base.endswith(('t', 'd')):
                        table_name_key = schema_base + 'en'
                    else:
                        table_name_key = schema_base + 'en'

                schemas[table_name_key] = value

        # Generate DDL for each schema/table
        all_fk_statements = []
        for table_name_key, schema_def in schemas.items():
            # CREATE TABLE
            create_sql, comments, fk_statements = self.generate_create_table(table_name_key, schema_def)
            ddl.append(create_sql)
            if comments:
                ddl.append("")
                ddl.extend(comments)
            ddl.append("")
            
            if fk_statements:
                all_fk_statements.extend(fk_statements)

            # INSERT Examples
            examples_data = None
            if isinstance(examples_dict, dict):
                # Look for examples with matching table name
                examples_data = examples_dict.get(table_name_key)

            if examples_data:
                inserts = self.generate_insert_examples(table_name_key, examples_data, schema_def)
                if inserts:
                    ddl.append("-- Example data")
                    ddl.extend(inserts)
                    ddl.append("")

            # INDEXES
            indexes = self.generate_index_statements(table_name_key, schema_def)
            if indexes:
                ddl.append("-- Indexes for performance")
                ddl.extend(indexes)
                ddl.append("")

        # Add all foreign keys at the end to avoid dependency issues during table creation
        if all_fk_statements:
            ddl.append("-- Foreign Key Constraints")
            ddl.extend(all_fk_statements)
            ddl.append("")

        return "\n".join(ddl)

    def save(self, output_path: str, table_name: str = None):
        """Sla DDL op als SQL bestand"""
        ddl = self.generate_all_ddl(table_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ddl)
        print(f"✅ DDL opgeslagen: {output_path}")


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='ODCS Contract to DDL Generator')
    parser.add_argument('contract', help='Pad naar het contract bestand (YAML/JSON)')
    parser.add_argument('output_pos', nargs='?', help='Output SQL bestand (optioneel, indien --out niet gebruikt wordt)')
    parser.add_argument('-o', '--out', help='Output SQL bestand')
    parser.add_argument('--db-type', default='postgresql', choices=['postgresql', 'mysql', 'sqlite', 'mssql'], 
                        help='Database type (standaard: postgresql)')

    args = parser.parse_args()

    contract_path = args.contract
    
    # Bepaal output pad: 1. --out vlag, 2. positionele argument, 3. default gebaseerd op contract naam
    if args.out:
        output_path = args.out
    elif args.output_pos:
        output_path = args.output_pos
    else:
        output_path = f"{Path(contract_path).stem}.sql"

    db_type = args.db_type

    print(f"🔄 Converteer contract naar DDL ({db_type})...")
    try:
        converter = ContractToDDL(contract_path, db_type)
        converter.save(output_path)
        print(f"✅ Klaar! DDL gegenereerd: {output_path}")
    except Exception as e:
        print(f"❌ Fout bij het genereren van DDL: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

