#!/usr/bin/env python3
"""
ODCS Contract to DDL Generator

Zet een Open Data Contract (YAML/JSON) automatisch om naar SQL DDL statements.
"""

import yaml
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
                return yaml.safe_load(f)
            return json.load(f)

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
        sql += "\n);"

        return sql, column_comments

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
        for field_name in properties.keys():
            if field_name != 'id':
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
        for table_name_key, schema_def in schemas.items():
            # CREATE TABLE
            create_sql, comments = self.generate_create_table(table_name_key, schema_def)
            ddl.append(create_sql)
            if comments:
                ddl.append("")
                ddl.extend(comments)
            ddl.append("")

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

        return "\n".join(ddl)

    def save(self, output_path: str, table_name: str = None):
        """Sla DDL op als SQL bestand"""
        ddl = self.generate_all_ddl(table_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ddl)
        print(f"✅ DDL opgeslagen: {output_path}")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Gebruik: python contract-to-ddl.py <contract.yaml> [output.sql] [--db-type postgresql|mysql|sqlite|mssql]")
        print("\nVoorbeelden:")
        print("  python contract-to-ddl.py datacontract/personen.yaml personen.sql")
        print("  python contract-to-ddl.py datacontract/personen.yaml personen.sql --db-type mysql")
        sys.exit(1)

    contract_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else f"{Path(contract_path).stem}.sql"
    db_type = 'postgresql'

    # Parse optional arguments
    if '--db-type' in sys.argv:
        idx = sys.argv.index('--db-type')
        if idx + 1 < len(sys.argv):
            db_type = sys.argv[idx + 1]

    print(f"🔄 Converteer contract naar DDL ({db_type})...")
    converter = ContractToDDL(contract_path, db_type)
    converter.save(output_path)
    print(f"✅ Klaar! DDL gegenereerd: {output_path}")


if __name__ == '__main__':
    main()

