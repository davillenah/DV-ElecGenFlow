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
- Nota: EPIC cerrada.

## EPIC-04.01: Electrical Load Modeling and Aggregation
- Estado: Hecho
- Release: v0.4.1
- Entrega: 
  - Agregación abajo→arriba sin duplicación.
  - Reporte de carga por tablero/alimentador (`load_report.json/.md`).
  - PF configurable + normalización de unidades (VA a HP).
  - Vistas: feeder, assembly, collapsed y top feeders.

## EPIC-04.02: Directed Network Topology Definition (DAG)
- Estado: Hecho
- Release: v0.4.2
- Entrega: 
  - Grafo dirigido de alimentación (DirectedElectricalGraphService).
  - Detección de raíces (roots), alcanzabilidad y ciclos.
  - Reportes técnicos (`dag_report.json/.md`).
  - Validación de nodos no alcanzables e islas.

## EPIC-04.03: Nominal Tables Management
- Estado: Hecho (v0)
- Release: v0.4.3
- Macro objetivo: Paso 8
- Requerimientos:
  - Tablas versionadas (cables, protecciones, métodos).
  - Overlays por fabricante.
  - Loader/validator de tablas (sin sizing automático).
  - Librería de componentes comerciales y base de datos (EPIC‑04.03+).
- Entrega:
  - Tablas versionadas (cables/protecciones/métodos)
  - Overlays por fabricante (estructura segmentada)
  - Loader/validator + lookup
  - Artifacts: nominal_snapshot / nominal_overlay_diff

## EPIC-04.04: Sizing and Validation Engine (modo validación)
- Estado: Pendiente
- Release: v0.4.4
- Macro objetivo: Paso 9
- Requerimientos:
  - CableContext (wire + protección + carga downstream).
  - Validaciones Ib/In/Iz + caída de tensión inicial.
  - Reportes de violaciones/warnings con evidencia.

## EPIC-05.00: Real Electrical Model (Lines/Loads)
- Estado: Pendiente
- Release: v0.5.0
- Macro objetivo: Paso 7
- Requerimientos:
  - Modelo eléctrico real de líneas y cargas P/Q.
  - Parámetros de instalación/longitud/impedancias.
  - Soporte Monofásico/Trifásico.

## EPIC-06.00: Rule & Constraint Engine (AEA/IEC)
- Estado: Pendiente
- Release: v0.6.0
- Macro objetivo: Pasos 9 y 11
- Requerimientos:
  - Motor de reglas normativas.
  - Trazabilidad y jerarquía normativa.
  - Ampacidad AEA/IEC parametrizable.

## EPIC-07.00: Simulation Engine (pandapower) + Metrics
- Estado: Pendiente
- Release: v0.7.0
- Macro objetivo: Paso 10
- Requerimientos:
  - Simulación y métricas técnicas reproducibles (Power Flow).
  - Cortocircuito IEC 60909.
  - Caída de tensión avanzada.

## EPIC-08.00: Generador de variantes
- Estado: Pendiente
- Requerimientos: Creación automática de alternativas de diseño.

## EPIC-09.00: Optimizer (ranking / Pareto)
- Estado: Pendiente
- Requerimientos: Algoritmos de selección de la mejor variante técnica/económica.

## EPIC-10.00: Scenario Manager
- Estado: Pendiente
- Requerimientos: Comparativa de resultados y snapshots de diseño.

## EPIC-11.00: Reporting & Exporting Engine (PDF/Excel/JSON)
- Estado: En Proceso
- Release: v0.11.0
- Macro objetivo: Paso 12
- Requerimientos:
  - Reporte PDF completo.
  - Export técnico Excel/JSON/CSV.
- Entrega:
  - v0.4.3 incluye un precursor PDF desde artifacts (ADR-0007).
  - Estado del motor final EPIC-11: Pendiente.

## EPIC-12.00: Factor de potencia, compensación y THD
- Estado: Pendiente
- Requerimientos: Cálculos de calidad de energía y compensación de reactiva.

## EPIC-13.00: Selectividad de protecciones y curvas de disparo
- Estado: Pendiente
- Requerimientos: Coordinación de protecciones.

## EPIC-14.00: Integración de sistemas renovables PV/BESS
- Estado: Pendiente
- Requerimientos: Modelado de generación distribuida y baterías.

## EPIC-15.00: Hardening industrial y optimización
- Estado: Pendiente
- Requerimientos: Performance y robustez del software.

## EPIC-17.00: Integration Layer (IFC/DXF/JSON Import-Export)
- Estado: Pendiente
- Release: v1.1.0
- Macro objetivo: Paso 13
- Requerimientos:
  - Export/bridge para planos (DXF/IFC u otros).
  - Mapeo tags → entidades CAD/BIM.
  - Planos eléctricos automáticos (unifilar/esquemas).

## EPIC-18.00: Control de acceso (RBAC) y Logs de auditoría
- Estado: Pendiente
- Requerimientos: Seguridad y trazabilidad de cambios de usuario.

## EPIC-20.00: Offline Interactive Report (HTML/CSS/JS)
- Estado: Pendiente
- Release: v2.1.0 (idea futura)
- Requerimientos:
  - Bundle offline navegable (archivos estáticos).
  - Visualizaciones interactivas (DAG/unifilar).