# RELEASE LOG

## v0.1.0
- EPIC-01.00: scaffolding profesional + gobernanza

## v0.2.0
- EPIC-02.00: contratos dominio + validación + manifest + CLI mínimo + CI QA

## v0.3.0
- EPIC-03.00: Elecboard IR v1
  - Modelo lógico estructural (boards, nodes, branches, loads, sources)
  - Validaciones estructurales
  - Tests unitarios + ejemplo JSON

## v0.4.0
- EPIC-04.00: DSL + Registry Integration Layer
  - Project loader (scan/import/build)
  - Registry bootstrap (SSoT = Board DSL)
  - Network compiler (validación estricta)
  - Adapter DSL→IR (compatible EPIC-03.00)
  - Out-of-service boards (no se consideran si no están en network/assembly)
  - Tests unitarios EPIC-04.00

## v0.4.1
- EPIC-04.01: Load aggregation abajo→arriba (sin duplicación)
- PF configurable + normalización de unidades
- Artifacts: `load_report.json` / `load_report.md`
- Vistas: feeder / assembly / collapsed / top feeders

## v0.4.2
- EPIC-04.02: DAG dirigido (roots/reachability/cycles/unreachable)
- Artifacts: `dag_report.json` / `dag_report.md`

## v0.4.3
- EPIC-04.03: Tablas nominales JSON v0 + overlays segmentados
- Artifacts: `nominal_snapshot.*` / `nominal_overlay_diff.*`
- EPIC-11 precursor: PDF consolidado desde artifacts (`engineering_report.pdf`)