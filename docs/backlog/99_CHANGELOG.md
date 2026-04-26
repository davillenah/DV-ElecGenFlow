# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- EPIC-04.01+: Network DSL runtime vía `build(network)` (fluent API) + fallback `build_network_snapshot()`
- EPIC-04.01+: Compilación con 2 modos:
  - DEV: reporta issues (sin frenar por el primer error)
  - RUNTIME: no detiene todo; salta links inválidos y degrada (disabled boards/columns/endpoints/entrypoints/terminals)
- EPIC-04.01+: Soporte de `from_source(...)` y `ends_at_load("LOAD-TAG")` para conexiones a cargas finales (board virtual `LOAD:<TAG>`)
- EPIC-04.01+: Adapter DSL→ElecboardIR: soporte de loads virtuales + `compile_report` embebido
- (placeholder) Component Library & Part Management | (EPIC-04.03)
- (placeholder) Sizing and Validation Engine | (EPIC-04.04)
- (placeholder) Real Electrical Model (Lines/Loads) | (EPIC-05.00)
- (placeholder) Rule & Constraint Engine (AEA/IEC) | (EPIC-06.00)
- (placeholder) Simulation Engine (pandapower) + Metrics | (EPIC-07.00)
- (placeholder) Variant Generator | (EPIC-08.00)
- (placeholder) Optimizer + Cost Model | (EPIC-09.00)
- (placeholder) Scenario Manager (Snapshot & Comparison) | (EPIC-10.00)
- (placeholder) Reporting & Exporting Engine (PDF/Excel/JSON) | (EPIC-11.00)
- (placeholder) Power Quality (THD/PF) | (EPIC-12.00)
- (placeholder) Protection Coordination & Tripping Curves | (EPIC-13.00)
- (placeholder) PV/BESS | (EPIC-14.00)
- (placeholder) Industrial Hardening | (EPIC-15.00)
- (placeholder) Release Candidate + Final Docs | (EPIC-16.00)
- (placeholder) Integration Layer (IFC/DXF/JSON Import-Export) | (EPIC-17.00)
- (placeholder) RBAC (Role-Based Access Control) & Audit Logs | (EPIC-18.00)
- (placeholder) Offline Interactive Report (HTML/CSS/JS) | (EPIC-20.00)

## - 2026-04-26
### Added
- EPIC-04.02: Directed Network Topology Definition (DAG)
- dag_report artifacts (`dag_report.json` / `dag_report.md`)
- Lógica de roots / reachability / cycles / unreachable
- Tests de integridad de grafo dirigidos

## - 2026-04-26
### Added
- EPIC-04.01: Electrical Load Modeling and Aggregation
- load_report artifacts (`load_report.json` / `load_report.md`)
- PF configurable + normalización de unidades (VA/kVA/MVA/W/kW/MW/HP)
- Vistas técnicas: feeder / assembly view / collapsed / top feeders

## - 2026-04-22
### Added
- Board DSL + Network DSL como entradas canónicas
- Registry auto-bootstrap (SSoT=Board DSL) + snapshot embebido
- Project loader automático (Project/Plant/Boards + ccm_assembly + network)
- Validación estricta del Network (error inmediato ante tags inexistentes)
- Adapter DSL→ElecboardIR (compatible EPIC-03.00)
- Tests unitarios + pipeline CI equivalente (ruff/black/mypy/pytest)

## - 2026-04-19
### Added
- Elecboard IR v1 (Logical Model): models + structural validation + tests + example JSON

## - 2026-04-17
### Added
- Núcleo de dominio (DDD): contratos pydantic (DesignProblem, Candidate, Results, Metrics, Constraints, Rules, Artifacts)
- Engine headless (orquestación stub) + RunManifest reproducible
- Loader de configuración YAML (default AR) y CLI mínimo
- Exportador de JSON Schema para contratos
- Tests unitarios base para validación
### Changed
- CI actualizado para ruff/black/mypy/pytest
- Versión del paquete a 0.2.0

## - 2026-04-17
### Added
- EPIC-01.00 completado: scaffolding profesional (estructura repo + gobernanza + docs base)
