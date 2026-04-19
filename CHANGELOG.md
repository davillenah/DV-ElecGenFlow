# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- (placeholder) Component Library & Part Management | (EPIC-4)
- (placeholder) Real Electrical Model (Lines/Loads) | (EPIC-5)
- (placeholder) Rule & Constraint Engine (AEA/IEC) | (EPIC-6)
- (placeholder) Simulation Engine (pandapower) + Metrics | (EPIC-7)
- (placeholder) Variant Generator | (EPIC-8)
- (placeholder) Optimizer + Cost Model | (EPIC-9)
- (placeholder) Scenario Manager (Snapshot & Comparison) | (EPIC-10)
- (placeholder) Reporting & Exporting Engine (PDF/Excel/JSON) | (EPIC-11)
- (placeholder) Power Quality (THD/PF) | (EPIC-12)
- (placeholder) Protection Coordination & Tripping Curves | (EPIC-13)
- (placeholder) PV/BESS | (EPIC-14)
- (placeholder) Industrial Hardening | (EPIC-15)
- (placeholder) Release Candidate + Final Docs | (EPIC-16)
- (placeholder) Integration Layer (IFC/DXF/JSON Import-Export) | (EPIC-17)
- (placeholder) RBAC (Role-Based Access Control) & Audit Logs | (EPIC-18)

## [0.3.0] - 2026-04-19
### Added
- Elecboard IR v1 (Logical Model): models + structural validation + tests + example JSON

## [0.2.0] - 2026-04-17
### Added
- Núcleo de dominio (DDD): contratos pydantic (DesignProblem, Candidate, Results, Metrics, Constraints, Rules, Artifacts)
- Engine headless (orquestación stub) + RunManifest reproducible
- Loader de configuración YAML (default AR) y CLI mínimo
- Exportador de JSON Schema para contratos
- Tests unitarios base para validación
### Changed
- CI actualizado para ruff/black/mypy/pytest
- Versión del paquete a 0.2.0

## [0.1.0] - 2026-04-17
### Added
- EPIC-0 completado: scaffolding profesional (estructura repo + gobernanza + docs base)