# PRODUCT BACKLOG — ElecGenFlow (MACRO requisitos técnicos)

> Este documento es el único punto MACRO (requerimientos técnicos).
> Cada macro requisito habilita uno o más pasos del ROADMAP.

## EPIC-01.00: Scaffolding + Governance
- Estado: Hecho
- Release: v0.1.0

## EPIC-02.00: Domain Core (DDD) + Contracts + Validation
- Estado: Hecho
- Release: v0.2.0

## EPIC-03.00: Elecboard IR v1 (Logical Graph)
- Estado: Hecho
- Release: v0.3.0

## EPIC-04.00: DSL + Registry Integration Layer
- Estado: Hecho
- Release: v0.4.0
- Nota: EPIC cerrada; no se reabre ni se “corrige” en backlog (solo mejoras futuras en EPICs siguientes)

## EPIC-04.01: Electrical Load Modeling and Aggregation
- Estado: Pendiente
- Release: v0.4.1
- Macro objetivo (ROADMAP): Paso 5
- Requerimientos:
  - Agregación abajo→arriba sin duplicación
  - Reporte de carga por tablero y por alimentador
  - Estructuras derivadas (LoadSummary) trazables

## EPIC-04.02: Directed Network Topology Definition (DAG)
- Estado: Pendiente
- Release: v0.4.2
- Macro objetivo (ROADMAP): Paso 6
- Requerimientos:
  - Grafo dirigido de alimentación
  - Detección de ciclos reales
  - Nodos no alcanzables + islas controladas
  - Separación topología vs flujo

## EPIC-04.03: Nominal Tables Management
- Estado: Pendiente
- Release: v0.4.3
- Macro objetivo (ROADMAP): Paso 8
- Requerimientos:
  - Tablas versionadas (cables, protecciones, métodos)
  - Overlays por fabricante
  - Loader/validator de tablas (sin sizing automático)

## EPIC-04.04: Sizing and Validation Engine (modo validación)
- Estado: Pendiente
- Release: v0.4.4
- Macro objetivo (ROADMAP): Paso 9
- Requerimientos:
  - CableContext (wire + protección + carga downstream)
  - Validaciones Ib/In/Iz + caída de tensión inicial
  - Reportes de violaciones/warnings con evidencia

## EPIC-05.00: Real Electrical Model (Lines/Loads)
- Estado: Pendiente
- Release: v0.5.0
- Macro objetivo (ROADMAP): Paso 7
- Requerimientos:
  - Modelo eléctrico real de líneas y cargas P/Q
  - Parámetros de instalación/longitud/impedancias
  - Integración con tablas nominales

## EPIC-06.00: Rule & Constraint Engine (AEA/IEC)
- Estado: Pendiente
- Release: v0.6.0
- Macro objetivo (ROADMAP): Pasos 9 y 11
- Requerimientos:
  - Motor de reglas normativas
  - Trazabilidad y jerarquía normativa

## EPIC-07.00: Simulation Engine (pandapower) + Metrics
- Estado: Pendiente
- Release: v0.7.0
- Macro objetivo (ROADMAP): Paso 10
- Requerimientos:
  - Simulación y métricas técnicas reproducibles

## EPIC-11.00: Reporting & Exporting Engine (PDF/Excel/JSON)
- Estado: Pendiente
- Release: v0.11.0
- Macro objetivo (ROADMAP): Paso 12
- Requerimientos:
  - Reporte PDF completo
  - Export técnico Excel/JSON
  - Plantillas y trazabilidad

## EPIC-17.00: Integration Layer (IFC/DXF/JSON Import-Export)
- Estado: Pendiente
- Release: v1.1.0
- Macro objetivo (ROADMAP): Paso 13
- Requerimientos:
  - Export/bridge para planos (DXF/IFC u otros)
  - Mapeo tags → entidades CAD/BIM

## EPIC-20.00 (nuevo): Offline Interactive Report (HTML/CSS/JS)
- Estado: Pendiente
- Release: v2.1.0 (idea futura)
- Macro objetivo (ROADMAP): Paso 14
- Requerimientos:
  - Bundle offline navegable
  - Visualizaciones (DAG/unifilar) + filtros + buscador
  - Cero backend (solo archivos estáticos)