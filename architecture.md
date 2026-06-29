# ODCS Architecture Overview

## High-Level Overview
The ODCS project follows a **contract-first** architecture where the data contract (`datacontract/personen.yaml`) serves as the single source of truth. This drives automated generation of:
- Database schema (SQL/DDL)
- OpenAPI API specification
- ER diagrams and documentation
- Kubernetes Helm charts

## Core Components
1. **Data Contract (YAML)**
   - Defines data structures, metadata, and SLA requirements
   - Serves as input for all automated generation processes

2. **Database Layer (PostgreSQL)
   - Stores personen/adres data
   - Auto-generated DDL from the contract
   - Includes indexes for performance optimization

3. **API Layer (PostgREST / GraphQL options)**
   - Exposes data via a RESTful API (PostgREST) and a GraphQL interface (PostGraphile)
   - *PostgREST:* Follows an "Auto-REST" pattern; exposes OpenAPI and supports resource embedding (e.g., `?select=*,related(*)`)
   - *PostGraphile:* Provides a flexible GraphQL interface derived from the database schema

4. **Documentation (Swagger UI)
   - Visualizes the generated OpenAPI spec
   - Provides interactive API testing capabilities
   - Includes ER diagrams for data structure visualization

5. **Deployment Stack**
   - Docker Compose for local development
   - Kubernetes Helm charts for production deployment
   - Ingress controllers for external access

6. **Validation & Testing**
   - **JMeter:** Performance and functional testing for both REST and GraphQL interfaces.
   - Test plans are located in the `tests/` directory.

## Data Flow
1. The YAML contract is processed by the `ddl-generator` to create SQL DDL
2. PostgREST converts the PostgreSQL database to a REST API using the **Auto-REST** pattern. This means endpoints and relationships are automatically derived from the database schema.
   - Example: `GET /adressen?select=*,personen(*)` fetches addresses and their related person records in one call.
3. OpenAPI spec is generated for documentation and testing
4. Swagger UI renders the OpenAPI spec into an interactive interface
5. Helm charts package the entire stack for Kubernetes deployment

## Diagrams
### High-Level Flow
```mermaid
graph TD
   A[Data Contract] --> B(DDL Generator)
   B --> C[PostgreSQL DB]
   C --> D(PostgREST API)
   C --> I(PostGraphile GraphQL)
   D --> E[OpenAPI Spec]
   E --> F(Swagger UI)
   I --> J[GraphQL Playground / GraphiQL]
   A --> G[Helm Charts]
   G --> H[Kubernetes Cluster]
```

### Deployment View (Docker)
```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "Internal Network"
            DB[(PostgreSQL DB<br/>Port 5432)]
            PGR(PostgREST API<br/>Port 3000)
            PGF(PostGraphile<br/>Port 5000)
            OAS(OpenAPI Server<br/>Port 80)
            SUI(Swagger UI<br/>Port 8080)
        end

        PGR --> DB
        PGF --> DB
        SUI -.-> OAS
    end

    Client([Client / Browser])
    Client -->|REST: 3000| PGR
    Client -->|GraphQL: 5000| PGF
    Client -->|Swagger: 8080| SUI
    
    subgraph "Volumes"
        DDL[./ddl-generator/generated/personen-ddl.sql]
        CONF[./configuratie/postgrest.conf]
        SPEC[./openapi-generator/generated/openapi-spec.yaml]
    end

    DDL -->|init| DB
    CONF -->|config| PGR
    SPEC -->|serve| OAS
```