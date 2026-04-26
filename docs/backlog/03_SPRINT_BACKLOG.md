# SPRINT BACKLOG — Detalle ejecutable por sprint

Histórico:
- Sprint EPIC-01.00: cerrado
- Sprint EPIC-02.00: cerrado
- Sprint EPIC-03.00: cerrado
- Sprint EPIC-04.00: cerrado
- Sprint EPIC-04.01: cerrado
- Sprint EPIC-04.02: cerrado
- Sprint EPIC-04.03: cerrado
- Sprint EPIC-11.00: parcial

---

## Sprint EPIC-04.01 — Agregación de cargas (PRIORIDAD 1)
Objetivo (ROADMAP Paso 5): carga abajo→arriba sin duplicación.

Entregables:
- Servicio LoadAggregationService
- LoadSummary por Board y por Feeder
- Artifacts: `load_report.json` + `load_report.md`
- Tests:
  - agregación simple y multi-nivel
  - consistencia (no duplicación)
  - casos con boards out_of_service

DoD:
- CI verde
- artifacts reproducibles
- trazabilidad por link/tag

---

## Sprint EPIC-04.02 — DAG eléctrico dirigido (PRIORIDAD 2)
Objetivo (ROADMAP Paso 6): grafo dirigido, ciclos y alcanzabilidad.

Entregables:
- DirectedElectricalGraphService:
  - reachable nodes
  - ciclo dirigido
  - nodos no alcanzables
- Artifacts: `dag_report.json` + `dag_report.md`
- Tests:
  - ciclo real
  - islas
  - alcanzabilidad desde fuentes

DoD:
- CI verde
- reporte claro por nodo/link
- no rompe IR v1

---

## Sprint EPIC-04.03 — Tablas nominales JSON (PRIORIDAD 3)
Objetivo (ROADMAP Paso 8): tablas mínimas versionadas.

Entregables:
- Schema v0 para:
  - cables
  - protecciones
  - métodos de instalación
- Loader + validator
- Artifacts: snapshot tablas cargadas
- Tests:
  - tabla válida/invalid
  - lookup por tag/familia/sección

DoD:
- CI verde
- versionado de tablas + compat

---

## Sprint EPIC-04.04 — Validación (sin sizing automático) (PRIORIDAD 4)
Objetivo (ROADMAP Paso 9): validar selección manual.

Entregables:
- CableContextResolver (wire + protección + carga)
- Validaciones iniciales:
  - Ib/In/Iz
  - caída de tensión inicial
- Reporte de violaciones/warnings:
  - severidad
  - evidencia normativa (placeholder trazable)

DoD:
- CI verde
- reportes reproducibles
- sin automatización de selección

---

## Sprint EPIC-05.00 — Modelo eléctrico real (PRIORIDAD 5)
Objetivo (ROADMAP Paso 7): P/Q, líneas, parámetros.

Entregables:
- Modelo de línea (R/X) + longitud + instalación
- Modelo de carga P/Q + perfiles (mínimo)
- Integración con tablas EPIC-04.03

DoD:
- CI verde
- integración con IR sin duplicación

---

## Sprint EPIC-07.00 — Simulación pandapower (PRIORIDAD 6)
Objetivo (ROADMAP Paso 10): simulación + KPIs.

Entregables:
- Translator IR → pandapower
- Flujo de carga + métricas base
- Artifacts: resultados + resumen

DoD:
- CI verde
- reproducible por manifest

---

## Sprint EPIC-11.00 — Reporte PDF (PRIORIDAD 7)
Objetivo (ROADMAP Paso 12): PDF final completo.

Entregables:
- Plantillas de reporte
- PDF con:
  - resumen
  - resultados
  - validaciones
  - anexos (tablas/listas)
- Export Excel/JSON complementario

DoD:
- CI verde
- PDF generado 100% desde artifacts

---

## Sprint EPIC-17.00 — Planos automáticos (PRIORIDAD 8)
Objetivo (ROADMAP Paso 13): generar planos eléctricos.

Entregables:
- Unifilar general
- Unifilar por tablero
- Listas de cables/borneras/dispositivos
- Export DXF/IFC (o formato definido)

DoD:
- CI verde
- trazabilidad tags→entidades

---

## Sprint EPIC-20.00 — Reporte Offline HTML (PRIORIDAD 9)
Objetivo (ROADMAP Paso 14): HTML/CSS/JS offline.

Entregables:
- Bundle estático offline
- Navegación por tableros/feeds
- Filtros de warnings/errores
- Visual DAG/unifilar (mínimo)

DoD:
- funciona offline
- sin backend
- reproducible desde artifacts