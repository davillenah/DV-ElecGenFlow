# CHECKLIST ElecGenFlow

## A) Motor generativo y de simulación
- [x] DesignProblem schema + validación (EPIC‑02.00)
- [ ] Generador de variantes (EPIC‑08.00)
- [ ] Rule engine normativo AEA/IEC (EPIC‑06.00)
- [ ] Evaluator con métricas reales - pandapower (EPIC‑07.00)
- [ ] Optimizer (ranking / Pareto) (EPIC‑09.00)
- [ ] Scenario Manager: Comparativa y snapshots (EPIC‑10.00)
- [x] Reproducibilidad (seed + manifest) (EPIC‑02.00)

## B) Elecboard DSL / IR & Componentes
- [ ] Librería de componentes comerciales y base de datos (EPIC‑04.00)
- [x] Modelo lógico Elecboard IR + grafo de red (EPIC-03.00)
- [ ] Traducción de IR a modelo pandapower (EPIC‑03.00/07.00)
- [ ] Cargas reales P/Q y modelado de líneas (EPIC-05.00)
- [ ] Soporte Monofásico/Trifásico (EPIC‑03.00/05.00)
- [ ] Validaciones de ratings de componentes (EPIC‑06.00)
- [ ] Board DSL canonical (EPIC‑04.00)
- [ ] Network DSL canonical (EPIC‑04.00)
- [ ] Registry schema + loader + validation (EPIC‑04.00)
- [ ] Adapter DSL→IR (EPIC‑04.00)
- [ ] Load aggregation abajo→arriba (EPIC‑04.01)
- [ ] DAG eléctrico dirigido (EPIC‑04.02)
- [ ] JSON bootstrap generator for Registry (EPIC‑04.00)
- [ ] Local DB evaluation (DuckDB vs SQLite) documented (EPIC‑04.XX)

## C) Cálculos avanzados y Normativa
- [ ] Caída de tensión AEA (EPIC‑06.00/07.00)
- [ ] Ampacidad AEA/IEC parametrizable (EPIC‑05.00/06.00)
- [ ] Cortocircuito IEC 60909 (EPIC‑07.00)
- [ ] Selectividad de protecciones y curvas de disparo (EPIC‑13.00)
- [ ] Factor de potencia, compensación y THD (EPIC‑12.00)
- [ ] Integración de sistemas renovables PV/BESS (EPIC‑14.00)

## D) Salida e Integración
- [ ] Motor de reportes ingenieriles PDF/Excel (EPIC‑11.00)
- [ ] Exportación de datos brutos JSON/CSV (EPIC‑11.00)
- [ ] Capa de integración CAD/BIM (IFC/DXF) (EPIC‑17.00)

## E) Software / DevOps
- [x] Repo scaffold (EPIC-1)
- [x] CI activo (ruff + black + mypy + pytest + coverage) (EPIC‑02.00)
- [x] Lint/format/tipado configurados (EPIC‑02.00)
- [x] Tests + coverage base (EPIC‑02.00)
- [x] Docs base + ADRs actualizados (EPIC‑01.00/16.00)
- [ ] Hardening industrial y optimización de performance (EPIC‑15.00)
- [ ] Control de acceso (RBAC) y Logs de auditoría (EPIC‑18.00)
