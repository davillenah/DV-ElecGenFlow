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

## v0.4.1 (pendiente)
- EPIC-04.01+: Network DSL runtime (build(network)) + degradación runtime (no bloqueante)
- EPIC-04.01+: Conexión a cargas finales: `ends_at_load` (board virtual `LOAD:<TAG>`)
- EPIC-04.01+: Reporte de compilación embebido (`compile_report`)
