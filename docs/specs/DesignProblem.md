# DesignProblem (EPIC-2)

## Objetivo
Definir el contrato de entrada del motor sin asumir datos eléctricos críticos.

## Principios
- No se asumen parámetros como Icc, esquemas de conexión (TT/TN/IT), longitudes, métodos de instalación, temperatura o resistividad del suelo.
- El detalle técnico se incorpora de forma incremental en la **EPIC-3 (Elecboard IR)** y la **EPIC-5 (Modelo Eléctrico)**.

## Campos
- `problem_id`, `name`, `description`
- `locale` (AR por defecto)
- `standards` (AEA/IEC declarativo)
- `seed` (reproducibilidad)
- `objectives` / `constraints` (opcionales, no se asumen por defecto)
- `payload` (extensión: IRs, requirements, etc.)
