# Registry — schema de tags + estrategia JSON/local DB + migraciones

---

## 1. Objetivo
El **Registry** es la fuente de verdad para identificar y vincular por TAG/ID:

- Tableros (**board tags**)
- Columnas/Salidas (**column tags**) — opcional por tablero
- Protecciones (**protection tags**)
- Borneras/Terminales (**terminal tags**)
- Conductores/Cables (**wire tags**)

**El Registry NO contiene lógica de cálculo.**  
Solo referencias, metadatos nominales y material de soporte para validaciones.

---

## 2. Principios
- **Reference-first:** el proyecto declara vínculos por TAGs.
- **Sin duplicación:** el cable no “tiene” protección ni carga; solo referencia IDs/tags.
- **Cargas viven abajo:** se definen en Board DSL (circuitos/subcircuitos).
- **Contexto derivado:** el motor reconstruye CableContext/LinkContext al consultar.

---

## 3. Estrategia de datos (por etapas)

### Etapa A — Prototipo (HOY)
- El Registry se materializa como **archivos JSON versionados** (sin DB real).
- Se permite autogeneración inicial (bootstrap) a partir de:
  - Board DSL (tableros y tags declarados)
  - Network DSL (links entre tags)

✅ En esta etapa, el schema y ejemplos viven en este `.md`.  
📌 Los `.json` reales se crean más adelante en EPIC‑04.03/04.04.

### Etapa B — Local DB (más adelante)
- Cuando el volumen de tablas/consultas crezca, se migra a DB embebida.
- Recomendación:
  - **DuckDB** para analítica y agregaciones (tablas nominales / catálogos).
  - **SQLite** como alternativa para persistencia simple tipo “app storage”.

### Etapa C — DB oficial (mucho más adelante)
- **PostgreSQL** como system-of-record para entorno web/multiusuario; DuckDB puede mantenerse para analítica.

### Etapa D — Web (futuro)
- Migración a Web (posible Flask). Fuera de alcance actual.

---

## 4. Estructura mínima (JSON) — versión v0 (documental)
Esta sección define **cómo serán** los JSON versionados del Registry.

### 4.1 boards.json
```json
{
  "version": "v0",
  "boards": [
    { "tag": "TG-PLANTA", "type": "BOARD", "meta": {} },
    { "tag": "TS-FUERZA", "type": "BOARD", "meta": {} }
  ]
}
```

### 4.2 terminals.json (borneras / puntos de conexión)
```json
{
  "version": "v0",
  "terminals": [
    { "board": "TS-FUERZA", "tag": "RED-PUBLICA", "meta": {} },
    { "board": "TS-FUERZA", "tag": "IG", "meta": {} }
  ]
}
```

### 4.3 columns.json (opcional por tablero)
```json
{
  "version": "v0",
  "columns": [
    { "board": "TGBT", "tag": "COL-01", "meta": {} },
    { "board": "TGBT", "tag": "COL-02", "meta": {} }
  ]
}
```

### 4.4 protections.json
```json
{
  "version": "v0",
  "protections": [
    {
      "board": "TGBT",
      "tag": "MCCB-49",
      "kind": "MCCB",
      "rating": { "amps": 250, "poles": 4 },
      "meta": {}
    }
  ]
}
```

### 4.5 wires.json
```json
{
  "version": "v0",
  "wires": [
    {
      "tag": "W123",
      "family": "CU-XLPE",
      "section_mm2": 25,
      "install": "BANDEJA",
      "meta": {}
    }
  ]
}
```

## 5. Ejemplo de Network DSL (usa SOLO referencias)
```python
network.supply_from("TG-PLANTA", "DOS") \
       .to("TS-FUERZA", "RED-PUBLICA") \
       .with_wire("W123") \
       .done()
```

## 6. Ubicación recomendada de archivos (cuando se creen)
Cuando pase EPIC‑04.03/04.04, se recomienda crear:

```text
data/registry/v0/boards.json
data/registry/v0/terminals.json
data/registry/v0/columns.json
data/registry/v0/protections.json
data/registry/v0/wires.json
```

**Nota**: En fase prototipo, pueden generarse automáticamente desde DSL y guardarse ahí.

## 7. Compatibilidad con el motor (Adapter)
El Adapter (EPIC‑04.00) consume:

- Board DSL snapshot (tableros y circuitos)
- Network DSL links (directed supply graph)
- Registry JSON (o snapshot embebido)

Y produce una representación interna compatible con EPIC‑03.00, sin duplicar cargas.

## 8. Nota de diseño
El Registry es infraestructura. No debe mezclar:

- Reglas normativas (EPIC‑04.04+)
- Dimensionamiento automático (EPIC‑05+)
- Optimización de costos (EPIC‑09+)

- **Ahora:** el JSON se documenta dentro del `.md` como schema + ejemplos (como arriba).  
- **Después:** sí, se crean archivos reales `.json` en `data/registry/v0/` (y el loader los consume).