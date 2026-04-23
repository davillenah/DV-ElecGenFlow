# ROADMAP — ElecGenFlow

## Objetivo final (producto)
1) Generar **Reporte PDF** completo del análisis eléctrico (MT/BT) con trazabilidad.
2) Generar **Planos eléctricos automáticamente** (unifilar, esquemas, listados y referencias).
3) Generar **Reporte interactivo OFF‑LINE** (HTML/CSS/JS) navegable (sin servidor).

---

## Paso a paso (pipeline end-to-end)

### 0) Setup / Proyecto
- Detectar y cargar proyecto desde estructura `Project/Plant/...`
- Validar que el proyecto es “reproducible” (manifest + seed).

### 1) Ingesta canónica (DSL)
- Cargar Board DSL (tableros/circuitos/subcircuitos).
- Cargar Assemblies (TGBT/CCM + columnas).
- Cargar Network DSL (links dirigidos, manuales y explícitos).

### 2) Registry (SSoT)
- Auto‑bootstrap del Registry a partir de Board DSL + Assemblies.
- Exponer conectables (boards / columns / protections / terminals / loads).
- Snapshot del registry para auditoría/debug.

### 3) Compilación de red (DEV / RUNTIME)
- Modo DEV: detectar y reportar inconsistencias (issues completos).
- Modo RUNTIME: no abortar; degradar/skip de elementos inválidos y continuar.

### 4) Adapter a IR estructural (ElecboardIR)
- Convertir DSL + Registry + Network compilada a grafo lógico (IR).
- Mantener compatibilidad estructural y trazabilidad (meta).

### 5) Agregación de cargas (abajo → arriba)
- Agregar cargas desde circuitos/subcircuitos hacia buses/boards upstream.
- Prohibido persistir duplicación (solo derivado).

### 6) Topología dirigida (DAG eléctrico)
- Construir grafo dirigido de alimentación.
- Detectar ciclos reales y nodos no alcanzables.
- Separar topología física vs flujo eléctrico.

### 7) Modelo eléctrico real (Lines/Loads)
- Materializar cargas P/Q reales, factores, perfiles.
- Materializar líneas (impedancias, longitudes, instalación).

### 8) Tablas nominales / Catálogos
- Ingesta de tablas versionadas (cables, protecciones, métodos, condiciones).
- Overlay de catálogos por fabricante/familia/modelo.

### 9) Validación técnica (sin automatizar todavía)
- Validaciones Ib/In/Iz, caída de tensión inicial, coherencia cable/protección/carga.
- Reportar violaciones y warnings con trazabilidad normativa.

### 10) Simulación + métricas (pandapower)
- Flujo de carga, pérdidas, caídas, carga de trafos, etc.
- Métricas y KPIs técnicos.

### 11) Coordinación de protecciones (futuro)
- Selectividad, curvas, coordinación (tripping curves).
- Reporte técnico de coordinación.

### 12) Reporte PDF (objetivo final #1)
- Reporte PDF completo:
  - resumen ejecutivo
  - detalle por tablero/feeder
  - validaciones + trazas normativas
  - resultados de simulación
  - anexos (tablas / listas)

### 13) Planos automáticos (objetivo final #2)
- Generar:
  - unifilar general
  - unifilar por tablero
  - esquemas de control (cuando aplique)
  - listas de cables / borneras / dispositivos
- Salida en formatos CAD/BIM definidos (etapa integración).

### 14) Reporte interactivo offline (objetivo final #3)
- Generar bundle HTML/CSS/JS:
  - navegación por tableros/feeds
  - filtros (warnings/errores)
  - vistas de DAG/unifilar
  - offline (sin backend)

---

## Estado actual (resumen)
- v0.4.0 completó la base de entrada canónica (DSL + Registry + Adapter + tests). [1](https://onedrive.live.com/?id=208775ff-41a4-49af-93c7-6fba5522804f&cid=8ee4e9ff1a66676a&web=1)
- Próximo: cargas (04.01) y DAG (04.02), luego tablas (04.03) y validación (04.04).