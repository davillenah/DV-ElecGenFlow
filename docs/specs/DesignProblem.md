# DesignProblem (EPIC-02.00)

## Objetivo
Definir el contrato de entrada del motor sin asumir datos eléctricos críticos.

## Principios
- No se asumen parámetros como Icc, esquemas de conexión (TT/TN/IT), longitudes, métodos de instalación, temperatura o resistividad del suelo.
- El detalle técnico se incorpora de forma incremental en la **EPIC-03.00 (Elecboard IR)** y la **EPIC-05.00 (Modelo Eléctrico)**.

## Campos
- `problem_id`, `name`, `description`
- `locale` (AR por defecto)
- `standards` (AEA/IEC declarativo)
- `seed` (reproducibilidad)
- `objectives` / `constraints` (opcionales, no se asumen por defecto)
- `payload` (extensión: IRs, requirements, etc.)

## payload (extensión)
Se adopta `payload` como contenedor de entradas canónicas:

- `payload.dsl.boards`: snapshot serializable de Board DSL (tableros y circuitos)
- `payload.dsl.network`: links dirigidos (supply_from → to → wire)
- `payload.registry`: referencia a DB/JSON o snapshot mínimo de tags y componentes

El motor construye el IR lógico desde estas entradas mediante un Adapter (EPIC-04.00).