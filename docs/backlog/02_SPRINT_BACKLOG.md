# SPRINT BACKLOG

Histórico:
- Sprint EPIC-03.00: cerrado.
- Sprint EPIC-02.00: cerrado.
- Sprint EPIC-01.00: cerrado.
- Sprint EPIC-04.00: cerrado.

## Próximos Sprints (post-EPIC-04.00)

### Sprint EPIC-04.01 — Agregación de Cargas (PRIORIDAD 1)
Objetivo: propagar cargas desde el nivel más bajo hacia arriba por topología dirigida,
sin persistir duplicación (solo derivado).

Entregables:
- LoadAggregationService (abajo → arriba)
- Reporte de carga por tablero y por alimentador (artefactos)
- Mantener compatibilidad con Elecboard IR v1 (EPIC-03.00)

### Sprint EPIC-04.02 — DAG Eléctrico Dirigido (PRIORIDAD 2)
Objetivo: interpretar la red como grafo dirigido de alimentación (DAG),
detectar ciclos y nodos no alcanzables.

Entregables:
- DirectedElectricalGraphService (alcanzabilidad + ciclos)
- Validación de nodos desconectados
- Base para sizing/validación normativa futura

### Sprint EPIC-04.03 — Tablas nominales en JSON (PRIORIDAD 3)
Objetivo: comenzar pruebas reales con datos técnicos, sin DB formal.

Entregables (JSON versionado):
- Cables: secciones, ampacidad nominal, material, instalación (mínimo)
- Protecciones: ratings nominales (mínimo)
- Métodos de instalación / condiciones (mínimo)

### Sprint EPIC-04.04 — Validación de selección (sin sizing automático) (PRIORIDAD 4)
Objetivo: validar lo seleccionado por el usuario (sin proponer).

Entregables:
- Reglas Ib/In/Iz iniciales
- Reporte de advertencias/violaciones trazables
- Sin automatización/dimensionamiento todavía

## Notas de alcance (IMPORTANTE)
- Por ahora NO se implementa Web.
- Por ahora NO se implementa DB oficial (solo JSON y snapshots).
- Más adelante: DB local (DuckDB recomendado para analítica) y luego DB oficial (PostgreSQL).