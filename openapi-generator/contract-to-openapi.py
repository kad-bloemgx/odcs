#!/usr/bin/env python3
"""
ODCS Contract to OpenAPI Spec Generator

Zet een Open Data Contract (YAML/JSON) automatisch om naar OpenAPI 3.0.3 spec.
"""

import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class ContractToOpenAPI:
    def __init__(self, contract_path: str):
        """Laad contract van YAML of JSON"""
        self.contract = self._load_contract(contract_path)
        self.spec = self._create_base_spec()

    def _load_contract(self, path: str) -> Dict[str, Any]:
        """Laad contract YAML/JSON"""
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                return yaml.safe_load(f)
            return json.load(f)

    def _create_base_spec(self) -> Dict[str, Any]:
        """Creëer basis OpenAPI structure"""
        contract = self.contract

        return {
            'openapi': '3.0.3',
            'info': {
                'title': contract.get('name', 'ODCS API'),
                'description': contract.get('description', ''),
                'version': contract.get('version', '1.0.0'),
                'contact': {
                    'name': contract.get('publisher', 'Kadaster'),
                    'email': contract.get('contactPoint', 'data@example.nl')
                },
                'license': {
                    'name': contract.get('license', 'CC0 1.0'),
                    'url': contract.get('licenseUrl', 'https://creativecommons.org/publicdomain/zero/1.0/')
                }
            },
            'servers': contract.get('servers', [
                {'url': 'https://api.example.nl/v1', 'description': 'Production'},
                {'url': 'https://api-dev.example.nl/v1', 'description': 'Development'}
            ]),
            'tags': self._build_tags(),
            'paths': self._build_paths(),
            'components': self._build_components(),
            'x-contract': {
                'sla': contract.get('sla', {}),
                'freshness_max_hours': contract.get('freshness_max_hours', 24),
                'version': contract.get('version', '1.0.0'),
                'effective_date': contract.get('issued', datetime.now().isoformat())
            }
        }

    def _build_tags(self) -> List[Dict[str, str]]:
        """Bouw tags uit contract"""
        return [
            {'name': 'Datasets', 'description': 'Dataset operations'},
            {'name': 'Metadata', 'description': 'Dataset metadata operations'},
            {'name': 'Health', 'description': 'API health and status'}
        ]

    def _build_paths(self) -> Dict[str, Any]:
        """Bouw API paths uit contract"""
        paths = {}

        # List datasets
        paths['/datasets'] = {
            'get': {
                'tags': ['Datasets'],
                'summary': 'List all available datasets',
                'operationId': 'listDatasets',
                'parameters': self._build_list_params(),
                'responses': {
                    '200': {
                        'description': 'List of datasets',
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/DatasetList'}
                            }
                        }
                    },
                    '429': {'description': 'Rate limit exceeded'},
                    '503': {'description': 'Service temporarily unavailable'}
                }
            }
        }

        # Get dataset
        paths['/datasets/{datasetId}'] = {
            'get': {
                'tags': ['Datasets'],
                'summary': 'Get dataset by ID',
                'operationId': 'getDataset',
                'parameters': [
                    {
                        'name': 'datasetId',
                        'in': 'path',
                        'required': True,
                        'schema': {'type': 'string'}
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Dataset metadata',
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/Dataset'}
                            }
                        }
                    },
                    '404': {'description': 'Dataset not found'},
                    '410': {'description': 'Dataset version is deprecated'}
                }
            }
        }

        # Get dataset data
        paths['/datasets/{datasetId}/data'] = {
            'get': {
                'tags': ['Datasets'],
                'summary': f"Download dataset (formats: {', '.join(self.contract.get('formats', ['json', 'csv', 'parquet']))})",
                'operationId': 'getDatasetData',
                'parameters': [
                    {'name': 'datasetId', 'in': 'path', 'required': True, 'schema': {'type': 'string'}},
                    {
                        'name': 'format',
                        'in': 'query',
                        'schema': {
                            'type': 'string',
                            'enum': self.contract.get('formats', ['json', 'csv', 'parquet'])
                        }
                    },
                    {'name': 'limit', 'in': 'query', 'schema': {'type': 'integer', 'default': 10000}},
                    {'name': 'offset', 'in': 'query', 'schema': {'type': 'integer', 'default': 0}}
                ],
                'responses': {
                    '200': {'description': 'Dataset records'},
                    '400': {'description': 'Invalid parameters'},
                    '429': {'description': 'Rate limit exceeded'}
                }
            }
        }

        # Get schema
        paths['/datasets/{datasetId}/schema'] = {
            'get': {
                'tags': ['Metadata'],
                'summary': 'Get JSON schema for dataset',
                'operationId': 'getDatasetSchema',
                'parameters': [
                    {'name': 'datasetId', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}
                ],
                'responses': {
                    '200': {'description': 'JSON Schema for dataset'}
                }
            }
        }

        # Get versions
        paths['/datasets/{datasetId}/versions'] = {
            'get': {
                'tags': ['Metadata'],
                'summary': 'List all versions of a dataset',
                'operationId': 'listDatasetVersions',
                'parameters': [
                    {'name': 'datasetId', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}
                ],
                'responses': {
                    '200': {
                        'description': 'List of versions',
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/VersionList'}
                            }
                        }
                    }
                }
            }
        }

        # Health check
        paths['/health'] = {
            'get': {
                'tags': ['Health'],
                'summary': 'API health check',
                'operationId': 'getHealth',
                'responses': {
                    '200': {
                        'description': 'API is healthy',
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/HealthStatus'}
                            }
                        }
                    },
                    '503': {'description': 'Service unhealthy'}
                }
            }
        }

        return paths

    def _build_list_params(self) -> List[Dict[str, Any]]:
        """Bouw query parameters voor list endpoint"""
        return [
            {
                'name': 'limit',
                'in': 'query',
                'schema': {'type': 'integer', 'default': 20, 'minimum': 1}
            },
            {
                'name': 'offset',
                'in': 'query',
                'schema': {'type': 'integer', 'default': 0}
            },
            {
                'name': 'search',
                'in': 'query',
                'schema': {'type': 'string'}
            }
        ]

    def _build_components(self) -> Dict[str, Any]:
        """Bouw components/schemas"""
        keywords = self.contract.get('keywords', [])

        return {
            'schemas': {
                'DatasetList': {
                    'type': 'object',
                    'properties': {
                        'data': {
                            'type': 'array',
                            'items': {'$ref': '#/components/schemas/DatasetSummary'}
                        },
                        'total': {'type': 'integer'},
                        'limit': {'type': 'integer'},
                        'offset': {'type': 'integer'}
                    }
                },
                'DatasetSummary': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string'},
                        'name': {'type': 'string'},
                        'description': {'type': 'string'},
                        'publisher': {'type': 'string'},
                        'license': {'type': 'string', 'format': 'uri'},
                        'tags': {'type': 'array', 'items': {'type': 'string'}},
                        'issued': {'type': 'string', 'format': 'date-time'},
                        'modified': {'type': 'string', 'format': 'date-time'},
                        'record_count': {'type': 'integer'}
                    }
                },
                'Dataset': {
                    'allOf': [
                        {'$ref': '#/components/schemas/DatasetSummary'},
                        {
                            'type': 'object',
                            'properties': {
                                'contactPoint': {'type': 'string', 'format': 'email'},
                                'language': {'type': 'string'},
                                'formats': {
                                    'type': 'array',
                                    'items': {'type': 'string'},
                                    'example': self.contract.get('formats', ['json', 'csv', 'parquet'])
                                },
                                'sla': {'$ref': '#/components/schemas/SLA'},
                                'last_indexed': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    ]
                },
                'SLA': {
                    'type': 'object',
                    'properties': {
                        'availability_target': {
                            'type': 'string',
                            'example': self.contract.get('availability_target', '99.5% monthly')
                        },
                        'freshness_max_hours': {
                            'type': 'integer',
                            'example': self.contract.get('freshness_max_hours', 24)
                        },
                        'response_time_p99_ms': {
                            'type': 'integer',
                            'example': self.contract.get('response_time_p99_ms', 500)
                        }
                    }
                },
                'VersionList': {
                    'type': 'object',
                    'properties': {
                        'versions': {
                            'type': 'array',
                            'items': {'$ref': '#/components/schemas/DatasetVersion'}
                        }
                    }
                },
                'DatasetVersion': {
                    'type': 'object',
                    'properties': {
                        'version': {'type': 'string'},
                        'released': {'type': 'string', 'format': 'date-time'},
                        'changelog': {'type': 'string'},
                        'record_count': {'type': 'integer'},
                        'status': {
                            'type': 'string',
                            'enum': ['current', 'deprecated', 'archived']
                        }
                    }
                },
                'HealthStatus': {
                    'type': 'object',
                    'properties': {
                        'status': {
                            'type': 'string',
                            'enum': ['healthy', 'degraded', 'unhealthy']
                        },
                        'timestamp': {'type': 'string', 'format': 'date-time'},
                        'components': {'type': 'object'},
                        'response_time_ms': {'type': 'number'}
                    }
                }
            }
        }

    def get_spec(self) -> Dict[str, Any]:
        """Retourneer volledige spec"""
        return self.spec

    def save(self, output_path: str):
        """Sla spec op als YAML"""
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.spec, f, default_flow_style=False, sort_keys=False)
        print(f"✅ OpenAPI spec opgeslagen: {output_path}")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Gebruik: python contract-to-openapi.py <contract.yaml> [output.yaml]")
        print("\nVoorbeeld:")
        print("  python contract-to-openapi.py open-data-contract.md openapi-spec.yaml")
        sys.exit(1)

    contract_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'generated-openapi-spec.yaml'

    print(f"🔄 Converteer contract naar OpenAPI spec...")
    converter = ContractToOpenAPI(contract_path)
    converter.save(output_path)
    print(f"✅ Klaar! OpenAPI spec gegenereerd: {output_path}")


if __name__ == '__main__':
    main()

