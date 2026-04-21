# ROADMAP — elecgenflow

## Visión (2026)
ElecGenFlow es un motor generativo para redes eléctricas MT/BT con un principio rector:
**el usuario declara intención (DSL + tags); el motor resuelve contexto (IR + DB + servicios).**

## Capas (orden obligatorio)
1. **DSL de Tableros (Board DSL):** descripción interna de tableros y cargas finales.
2. **DSL de Red (Network DSL):** conectividad dirigida `supply_from(...).to(...).with_wire(...).done()`.
3. **Registry / Component Library:** IDs y tablas técnicas (cables, protecciones, gabinetes) + tags físicos.
4. **IR estructural del motor:** grafo validado + referencias a DB (sin duplicación).
5. **Servicios de ingeniería:** agregación de cargas, validación DAG, sizing, trazabilidad normativa.
6. **Simulación / optimización:** pandapower, métricas, variantes, Pareto.

## Releases (SemVer pre-1.0)
- v00.01.00 — EPIC-01.0: Scaffolding + Governance ✅
- v00.02.00 — EPIC-02.0: Domain Core (DDD) + Contracts + Validation ✅
- v00.03.00 — EPIC-03.0: Elecboard IR v1 (Logical Graph) ✅
- v00.04.00 — EPIC-04.0: DSL + Registry Integration Layer
    - Board DSL canonical
    - Network DSL canonical (directed)
    - Registry schema (tags + components references)
    - IR Adapter (DSL → IR) + validación de referencias
- v00.04.01 — EPIC-04.1: Electrical Load Modeling and Aggregation
    - Carga abajo → arriba (sin persistencia duplicada)
    - Reporte de carga por tablero y por alimentador
- v00.04.02 — EPIC-04.2: Directed Network Topology Definition
    - Grafo dirigido (DAG) para alimentación eléctrica
    - Detección de ciclos eléctricos reales y nodos no alcanzables
    - Separación entre topología física y flujo eléctrico
- v00.04.03 — EPIC-04.3: Nominal Tables Management
    - Tablas técnicas versionadas (cables, protecciones, métodos)
    - Catálogos (Schneider/Siemens/mix) como overlays
- v00.04.04 — EPIC-04.4: Sizing and Validation Engine
    - CableContext (wire + protecciones ref + carga)
    - Validaciones Ib/In/Iz + caída de tensión (inicial)
- v00.04.05 — EPIC-04.5: Regulatory Hierarchy and Traceability
- v00.04.06 — EPIC-04.6: Reporting and Alerts System
- v00.04.07 — EPIC-04.7: Preparation for Future Automation
- v00.05.00 — EPIC-05.0: Real Electrical Model (Lines/Loads)
- v00.06.00 — EPIC-06.0: Rule & Constraint Engine (AEA/IEC)
- v00.07.00 — EPIC-07.0: Simulation Engine (pandapower) + Metrics
- v00.08.00 — EPIC-08.0: Variant Generator
- v00.09.00 — EPIC-09.0: Optimizer + Cost Model
- v00.10.00 — EPIC-10.0: Scenario Manager (Snapshot & Comparison)
- v00.11.00 — EPIC-11.0: Reporting & Exporting Engine (PDF/Excel/JSON)
- v00.12.00 — EPIC-12.0: Power Quality (THD/PF)
- v00.13.00 — EPIC-13.0: Protection Coordination & Tripping Curves
- v00.14.00 — EPIC-14.0: PV/BESS
- v00.15.00 — EPIC-15.0: Industrial Hardening
- v01.00.00 — EPIC-16.0: Release Candidate + Final Docs
- v01.01.00 — EPIC-17.0: Integration Layer (IFC/DXF/JSON Import-Export)

### Post‑v1.0 / Ideas futuras (no comprometido)
- v01.02.00 — EPIC-18.0: RBAC (Role-Based Access Control) & Audit Logs
    - Implementación de lógica de roles (Admin, Editor, Viewer).
    - Middleware de autorización en el backend.
    - Registro de eventos críticos para auditoría (quién hizo qué y cuándo).
- v02.00.00 — EPIC-19.0: Persistent Data Migration & PostgreSQL Integration
    - Configuración de entorno de producción con PostgreSQL (Dockerización).
    - Migración de esquemas desde SQLite/DuckDB a Postgres (scripts de migración).
    - Optimización de tipos de datos (uso de JSONB para campos flexibles y UUIDs para llaves primarias).
    - Implementación de Connection Pooling para manejo eficiente de conexiones en Python.
- v02.01.00 — EPIC-20.0: Frontend Modernization with React & Global State
    - Migración de vistas estáticas o templates a componentes funcionales en React.
    - Consumo de la API de Python mediante TanStack Query (React Query) para sincronización de datos.
    - Gestión de estado global (Zustand o Context API) para sesiones de usuario y preferencias.
- v02.02.00 — EPIC-21.0: Real-time & Advanced Monitoring
    - Integración de WebSockets (FastAPI/Flask-SocketIO) para actualizaciones en tiempo real en el frontend.
    - Panel de monitoreo de salud de la base de datos y logs centralizados.
