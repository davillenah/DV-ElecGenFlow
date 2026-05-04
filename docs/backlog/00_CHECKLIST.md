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
- [x] Registry schema + loader + validation (tags + referencias técnicas) (EPIC‑04.00)
- [x] Adapter DSL→IR con validación de referencias (EPIC‑04.00)
- [x] JSON bootstrap snapshot for Registry (EPIC‑04.00)
- [x] Network DSL runtime vía `build(network)` + fallback snapshot (EPIC‑04.01+)
- [x] Compiler DEV/RUNTIME (DEV reporta issues; RUNTIME degrada/skip y continúa) (EPIC‑04.01+)
- [x] Conexión a cargas finales `ends_at_load()` + board virtual `LOAD:<TAG>` (EPIC‑04.01+)

## 3. Lógica de Red y Grafo Eléctrico
- [x] Load aggregation abajo→arriba (sin duplicación) + artifacts `load_report.json/.md` (EPIC‑04.01)
- [x] PF configurable en `configs/default_ar.yaml` (EPIC‑04.01)
- [x] Normalización unidades (VA/kVA/MVA/W/kW/MW/HP) + tests (EPIC‑04.01)
- [x] Vista por feeder + assembly view + collapsed + top feeders (EPIC‑04.01)
- [x] DirectedElectricalGraphService (roots/reachability/cycles/unreachable) (EPIC‑04.02)
- [x] Artifacts `dag_report.json/.md` (EPIC‑04.02)
- [x] Tests DAG (roots, cycles, unreachable) (EPIC‑04.02)

## 4. Componentes y Base de Datos Técnica
- [ ] Traducción de IR a modelo pandapower (EPIC‑07.00)
- [ ] Cargas reales P/Q y modelado de líneas (EPIC‑05.00)
- [ ] Soporte Monofásico/Trifásico completo en modelo eléctrico (EPIC‑05.00)
- [x] Tablas nominales JSON versionadas v0 (cables/protecciones/métodos) (EPIC‑04.03)
- [x] Overlays por fabricante (estructura segmentada) (EPIC‑04.03)
- [ ] Librería de componentes comerciales y base de datos (EPIC‑04.03+)
- [ ] Local DB evaluation (DuckDB vs SQLite) documented (EPIC‑04.XX)

## 5. Motor Generativo y Optimización
- [ ] Generador de variantes (EPIC‑08.00)
- [ ] Rule engine normativo AEA/IEC (EPIC‑06.00)
- [ ] Evaluator con métricas reales - pandapower (EPIC‑07.00)
- [ ] Optimizer (ranking / Pareto) (EPIC‑09.00)
- [ ] Scenario Manager: Comparativa y snapshots (EPIC‑10.00)

## 6. Cálculos de Ingeniería y Normativa
- [x] EPIC‑04.04: Validación inicial Ib vs Iz (base)
- [x] EPIC‑04.04: Auto‑sugerencia de sección mínima por ampacidad AEA (no vinculante)
- [x] EPIC‑04.04: Artifacts `sizing_report.*`, `cable_schedule.*` y `selected_wires.json`
- [ ] EPIC‑04.04+: Coordinación Ib/In/Iz (protección)
- [ ] EPIC‑04.04+: Derating completo k_group/k_temp/k_soil (grouped + condiciones)
- [ ] EPIC‑04.04/06.00: Caída de tensión inicial
- [ ] Validaciones de ratings de componentes (EPIC‑06.00)

## 7. Salida, Reportes e Integración
- [x] Precursor PDF desde artifacts: `engineering_report.pdf` (ADR‑0007)
- [ ] Motor de reportes ingenieriles PDF/Excel (EPIC‑11.00)
- [ ] Export técnico Excel/JSON/CSV (EPIC‑11.00)
- [ ] Planos eléctricos automáticos (unifilar/listados/esquemas) (EPIC‑17.00)
- [ ] Reporte interactivo OFF‑LINE (HTML/CSS/JS) (EPIC‑20.00)

---




