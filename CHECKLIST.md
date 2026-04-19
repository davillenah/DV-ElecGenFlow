# CHECKLIST ElecGenFlow

## A) Motor generativo y de simulación
- [x] DesignProblem schema + validación (EPIC-2)
- [ ] Generador de variantes (EPIC-8)
- [ ] Rule engine normativo AEA/IEC (EPIC-6)
- [ ] Evaluator con métricas reales - pandapower (EPIC-7)
- [ ] Optimizer (ranking / Pareto) (EPIC-9)
- [ ] Scenario Manager: Comparativa y snapshots (EPIC-10)
- [x] Reproducibilidad (seed + manifest) (EPIC-2)

## B) Elecboard DSL / IR & Componentes
- [ ] Librería de componentes comerciales y base de datos (EPIC-4)
- [x] Modelo lógico Elecboard IR + grafo de red (EPIC-3)
- [ ] Traducción de IR a modelo pandapower (EPIC-3/7)
- [ ] Cargas reales P/Q y modelado de líneas (EPIC-5)
- [ ] Soporte Monofásico/Trifásico (EPIC-3/5)
- [ ] Validaciones de ratings de componentes (EPIC-6)

## C) Cálculos avanzados y Normativa
- [ ] Caída de tensión AEA (EPIC-6/7)
- [ ] Ampacidad AEA/IEC parametrizable (EPIC-5/6)
- [ ] Cortocircuito IEC 60909 (EPIC-7)
- [ ] Selectividad de protecciones y curvas de disparo (EPIC-13)
- [ ] Factor de potencia, compensación y THD (EPIC-12)
- [ ] Integración de sistemas renovables PV/BESS (EPIC-14)

## D) Salida e Integración
- [ ] Motor de reportes ingenieriles PDF/Excel (EPIC-11)
- [ ] Exportación de datos brutos JSON/CSV (EPIC-11)
- [ ] Capa de integración CAD/BIM (IFC/DXF) (EPIC-17)

## E) Software / DevOps
- [x] Repo scaffold (EPIC-1)
- [x] CI activo (ruff + black + mypy + pytest + coverage) (EPIC-2)
- [x] Lint/format/tipado configurados (EPIC-2)
- [x] Tests + coverage base (EPIC-2)
- [x] Docs base + ADRs actualizados (EPIC-1/16)
- [ ] Hardening industrial y optimización de performance (EPIC-15)
- [ ] Control de acceso (RBAC) y Logs de auditoría (EPIC-18)
