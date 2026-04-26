# CHECKLIST ElecGenFlow

## 1. Infraestructura de Software y DevOps
- [x] Repo scaffold (EPIC‑01.00)
- [x] CI activo (ruff + black + mypy + pytest + coverage) (EPIC‑02.00)
- [x] Lint/format/tipado configurados (EPIC‑02.00)
- [x] Tests + coverage base (EPIC‑02.00)
- [x] Docs base + ADRs actualizados (EPIC‑01.00/EPIC‑03.00)
- [ ] Hardening industrial y optimización de performance (EPIC‑15.00)
- [ ] Control de acceso (RBAC) y Logs de auditoría (EPIC‑18.00)

## 2. Definición de Modelo y Entrada Canónica
- [x] DesignProblem schema + validación (EPIC‑02.00)
- [x] Reproducibilidad (seed + manifest) (EPIC‑02.00)
- [x] Modelo lógico Elecboard IR + grafo de red (EPIC‑03.00)
- [x] Board DSL canonical (EPIC‑04.00)
- [x] Network DSL canonical (directed) (EPIC‑04.00)
- [x] Registry schema + loader + validation (EPIC‑04.00)
- [x] Adapter DSL→IR con validación de referencias (EPIC‑04.00)
- [x] JSON bootstrap snapshot for Registry (EPIC‑04.00) *(snapshot embebido; JSON versionados llegan en 04.03/04.04)*
- [x] Network DSL runtime vía `build(network)` + fallback snapshot (EPIC‑04.01+)
- [x] Compiler DEV/RUNTIME (DEV reporta issues; RUNTIME degrada/skip y continúa) (EPIC‑04.01+)
- [x] Conexión a cargas finales `ends_at_load()` + board virtual `LOAD:<TAG>` (EPIC‑04.01+)

## 3. Lógica de Red y Grafo Eléctrico (Implementado en v0.4.1/0.4.2)
- [x] Load aggregation abajo→arriba (sin duplicación) + artifacts `load_report.json/.md` (EPIC‑04.01)
- [x] PF configurable en `configs/default_ar.yaml` (EPIC‑04.01)
- [x] Normalización unidades (VA/kVA/MVA/W/kW/MW/HP) + tests (EPIC‑04.01)
- [x] Vista por feeder + assembly view + collapsed + top feeders (EPIC‑04.01)
- [x] DirectedElectricalGraphService (roots/reachability/cycles/unreachable) (EPIC‑04.02)
- [x] Artifacts `dag_report.json/.md` (EPIC‑04.02)
- [x] Tests DAG (roots, cycles, unreachable) (EPIC‑04.02)
- [ ] DAG eléctrico dirigido (alcanzabilidad + ciclos + nodos no alcanzables) (EPIC‑04.02)

## 4. Componentes y Base de Datos Técnica
- [ ] Traducción de IR a modelo pandapower (EPIC‑03.00/EPIC‑07.00)
- [ ] Cargas reales P/Q y modelado de líneas (EPIC‑05.00)
- [ ] Soporte Monofásico/Trifásico (EPIC‑03.00/EPIC‑05.00)
- [ ] Tablas nominales JSON versionadas (cables/protecciones/métodos) (EPIC‑04.03)
- [ ] Librería de componentes comerciales y base de datos (EPIC‑04.03+)
- [ ] Local DB evaluation (DuckDB vs SQLite) documented (EPIC‑04.XX)

## 5. Motor Generativo y Optimización
- [ ] Generador de variantes (EPIC‑08.00)
- [ ] Rule engine normativo AEA/IEC (EPIC‑06.00)
- [ ] Evaluator con métricas reales - pandapower (EPIC‑07.00)
- [ ] Optimizer (ranking / Pareto) (EPIC‑09.00)
- [ ] Scenario Manager: Comparativa y snapshots (EPIC‑10.00)

## 6. Cálculos de Ingeniería y Normativa
- [ ] Validación técnica (Ib/In/Iz + caída de tensión inicial; sin sizing automático) (EPIC‑04.04)
- [ ] Validaciones de ratings de componentes (EPIC‑06.00)
- [ ] Caída de tensión AEA (EPIC‑06.00/EPIC‑07.00)
- [ ] Ampacidad AEA/IEC parametrizable (EPIC‑05.00/EPIC‑06.00)
- [ ] Cortocircuito IEC 60909 (EPIC‑07.00)
- [ ] Selectividad de protecciones y curvas de disparo (EPIC‑13.00)
- [ ] Factor de potencia, compensación y THD (EPIC‑12.00)
- [ ] Integración de sistemas renovables PV/BESS (EPIC‑14.00)

## 7. Salida, Reportes e Integración
- [ ] Motor de reportes ingenieriles PDF/Excel (EPIC‑11.00)
- [ ] Exportación de datos brutos JSON/CSV (EPIC‑11.00)
- [ ] Planos eléctricos automáticos (unifilar/listados/esquemas) (EPIC‑17.00)
- [ ] Reporte interactivo OFF‑LINE (HTML/CSS/JS) (EPIC‑20.00 / idea futura)

---

## ADDENDUM (pre-release v0.4.3) — Estado real de implementación

### EPIC-04.02 (DAG)
- [x] DirectedElectricalGraphService implementado (roots/reachability/cycles/unreachable)
- [x] Artifacts: `dag_report.json/.md`
- [x] Tests: roots, cycles, unreachable

> Nota: si existe un ítem duplicado de DAG en estado [ ], se considera redundante. El estado correcto es DONE.

### EPIC-04.03 (Nominal Tables)
- [x] Tablas nominales JSON v0: cables / protecciones / métodos
- [x] Overlays por fabricante (estructura segmentada)
- [x] Loader/validator + lookup + overlay diff artifacts
- [x] Artifacts: `nominal_snapshot.*` y `nominal_overlay_diff.*`

### EPIC-11 (Reporting)
- [x] Precursor PDF desde artifacts: `engineering_report.pdf` (ADR-0007)
- [ ] EPIC-11 “motor final” sigue pendiente (plantillas completas PDF/Excel/CSV)