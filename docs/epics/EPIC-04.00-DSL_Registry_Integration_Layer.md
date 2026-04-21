# EPIC-04.0 — DSL + Registry Integration Layer (Pivot post-EPIC-03.00)

- Prioridad: Muy Alta
- Estado: Pendiente
- Release: v0.4.0

## Objetivo
Formalizar Board DSL y Network DSL como entrada canónica post-EPIC-3.
Definir Registry schema (tags + referencias técnicas) y el Adapter DSL→IR.

## Alcance
- Board DSL canonical (tableros como archivos independientes)
- Network DSL canonical (directed):
  `network.supply_from(...).to(...).with_wire(...).done()`
- Registry schema versionado (board/column/protection/terminal/wire)
- Loader + validación de referencias (sin DB real; inicialmente JSON)
- Adapter DSL→IR con tests (coherencia, links dirigidos, referencias válidas)

## Entregables
- Especificación de tags (board/column/protection/terminal/wire)
- Esquema versionado de Registry (JSON Schema)
- Adapter con tests (links dirigidos + coherencia)
- Export/Import inicial a JSON (para pruebas)