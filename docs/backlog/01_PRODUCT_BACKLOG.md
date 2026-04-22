# PRODUCT BACKLOG — elecgenflow

> Nota:
> Los entregables detallados solo se listan para EPICs completadas
> o activamente en desarrollo. Las EPICs futuras se describen a nivel
> de objetivos hasta que entren en ejecución.

## EPIC-01.00: Scaffolding + Governance
- Prioridad: Alta
- Estado: Hecho
- Release: v0.1.0

## EPIC-02.00: Domain Core (DDD) + Contracts + Validation
- Prioridad: Muy Alta
- Estado: Hecho
- Release: v0.2.0
- Entregables:
  - Contratos pydantic (DesignProblem, Candidate, Constraints, Objectives, Metrics, Rules, Artifacts, Result)
  - Config loader YAML + defaults AR
  - RunManifest reproducible
  - Engine headless stub + CLI mínimo
  - Tests unitarios base + CI

## EPIC-03.00: Elecboard IR v1 (Logical Graph)
- Prioridad: Alta
- Estado: Hecho
- Release: v0.3.0
- Entregables:
  - Modelo lógico estructural del sistema eléctrico (Elecboard IR)
  - Entidades: Board, Node, Branch, Load, Source
  - Representación explícita como grafo
  - Validaciones estructurales:
    - conectividad
    - fases compatibles
    - nodos huérfanos
    - topología radial / islas
  - Serialización / deserialización del IR
  - Tests unitarios completos (casos válidos e inválidos)
  - Ejemplo JSON funcional del IR
  - Documentación técnica formal (EPIC-3)

## EPIC-04.00: DSL + Registry Integration Layer
- Prioridad: Muy Alta
- Estado: Hecho
- Release: v0.4.0
- Objetivo: definir entrada canónica por DSL y referencias
- Entregables:
  - Board DSL especificada
  - Network DSL dirigida especificada
  - Registry schema versionado
  - Adapter DSL→IR con validación de referencias

## EPIC-05.00: Real Electrical Model (Lines/Loads)
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.5.0

## EPIC-06.00: Rule & Constraint Engine (AEA/IEC)
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.6.0

## EPIC-07.00: Simulation Engine (pandapower) + Metrics
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.7.0

## EPIC-08.00: Variant Generator
- Prioridad: Media
- Estado: Pendiente
- Release: v0.8.0

## EPIC-09.00: Optimizer + Cost Model
- Prioridad: Media
- Estado: Pendiente
- Release: v0.9.0

## EPIC-10.00: Scenario Manager (Snapshot & Comparison)
- Prioridad: Media
- Estado: Pendiente
- Release: v0.10.0
- Objetivo: Persistencia y comparación técnica entre diferentes variantes y estados de red.

## EPIC-11.00: Reporting & Exporting Engine (PDF/Excel/JSON)
- Prioridad: Media
- Estado: Pendiente
- Release: v0.11.0
- Objetivo: Generación automatizada de reportes de ingeniería y exportación de datos brutos.

## EPIC-12.00: Power Quality (THD/PF)
- Prioridad: Media
- Estado: Pendiente
- Release: v0.12.0

## EPIC-13.00: Protection Coordination & Tripping Curves
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.13.0
- Objetivo: Estudio de selectividad y curvas de disparo para interruptores.

## EPIC-14.00: PV/BESS
- Prioridad: Baja
- Estado: Pendiente
- Release: v0.14.0

## EPIC-15.00: Industrial Hardening
- Prioridad: Media
- Estado: Pendiente
- Release: v0.15.0

## EPIC-16.00: Release Candidate + Final Docs
- Prioridad: Alta
- Estado: Pendiente
- Release: v1.0.0

## EPIC-17.00: Integration Layer (IFC/DXF/JSON Import-Export)
- Prioridad: Baja
- Estado: Pendiente
- Release: v1.1.0

## EPIC-18.00: RBAC (Role-Based Access Control) & Audit Logs
- Prioridad: Baja
- Estado: Pendiente
- Release: v1.2.0