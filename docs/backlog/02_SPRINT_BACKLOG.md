# SPRINT BACKLOG

Histórico:
- Sprint EPIC-03.00: cerrado.
- Sprint EPIC-02.00: cerrado.
- Sprint EPIC-01.00: cerrado.

## Próximos Sprints (post-EPIC-03.00 / Pivot EPIC-04.00)

### Sprint EPIC-04.00 — Adaptación del motor para DSL (PRIORIDAD 1)
Objetivo: permitir escribir proyectos con la forma solicitada (Board DSL + Network DSL) y
traducirlo a una representación interna compatible con el IR existente (EPIC-03.0).

Entregables:
- Board DSL canonical (tableros como archivos independientes)
- Network DSL canonical (supply_from → to → with_wire → done)
- Registry schema (tags) + loader/validation (sin DB real)
- Adapter DSL → IR (con validación de referencias)
- Topología dirigida (DAG lógico de alimentación) **sin cálculos automáticos aún**

### Sprint EPIC-04.03 — Tablas nominales en JSON (PRIORIDAD 2)
Objetivo: comenzar pruebas reales con datos técnicos, sin base de datos formal.

Entregables (JSON versionado):
- Cables: secciones, ampacidad nominal (tablas), material, instalación (mínimo)
- Protecciones: ratings nominales (mínimo para validar)
- Métodos de instalación / condiciones (mínimo)

### Sprint EPIC-04.04 — Validación de selección (sin dimensionamiento automático) (PRIORIDAD 3)
Objetivo: establecer reglas normativas para validar lo seleccionado por el usuario.

Entregables:
- Reglas de verificación: cable seleccionado vs protección vs carga downstream
- Reporte de advertencias/violaciones trazables
- Sin sizing automático (no propone cable ni protección todavía)

### Sprint EPIC-04.XX — Catálogo de fabricantes/modelos en JSON (PRIORIDAD 4)
Objetivo: preparar automatización futura sin comprometer el prototipo.

Entregables (JSON versionado):
- Fabricantes, familias, modelos, equivalencias
- Configuración de catálogo (ej. Schneider/Siemens/Mix)

## Notas de alcance (IMPORTANTE)
- Por ahora NO se implementa Web.
- Por ahora NO se implementa DB real (solo JSON).
- Más adelante: DB local (DuckDB recomendado para analítica) y luego DB oficial (PostgreSQL).
