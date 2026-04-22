# EPIC-04.0 — DSL + Registry Integration Layer (Pivot post-EPIC-03.00)

- Prioridad: Muy Alta
- Estado: Hecho [x]
- Release: v0.4.0

## 1. Objetivo
Formalizar los lenguajes **Board DSL** y **Network DSL** como las únicas entradas canónicas del sistema.
Establecer el **Board DSL como la Fuente Única de Verdad (SSoT)** para el Registry, permitiendo que el sistema
"bootstrapee" automáticamente el inventario técnico. El Network DSL deberá validar sus referencias en tiempo real
contra este Registry generado dinámicamente.

## 2. Alcance

### 2.1. Board DSL & Auto-Bootstrap (Registry Ingestion)
- **Board DSL Canonical:** Definición de tableros como archivos independientes que actúan como declaración de activos.
- **Mecanismo de Inferencia:** El motor procesa el Board DSL y genera automáticamente el **Registry** en memoria
  (mapeando `boards`, `columns`, `protections` y `terminals`).
- **Registro Automatizado:** El usuario NO escribe el Registry manualmente (ni JSON ni DB). El sistema lo deduce de
  los boards declarados.

### 2.2. Network DSL & Strict Validation
- **Network DSL (Directed):** Sintaxis fluida para definir el flujo eléctrico:

  `network.supply_from(...).column(...).protection(...).terminal(...).to(...).column(...).protection(...).terminal(...).with_wire(...).done()`

- **Validación de Referencias:** Si el Network DSL referencia un `tag` que NO fue declarado en el Board DSL (o inferido
  por el bootstrap), el sistema lanza un error inmediato de compilación/carga.

### 2.3. Registry Schema & Adapter
- **Registry Schema Versionado:** Estructura de tags y metadatos técnicos (board/column/protection/terminal/wire) para
  validación interna.
- **Adapter DSL → IR (Intermediate Representation):** Transformador de las declaraciones DSL en un grafo compatible con
  Elecboard IR v1 (EPIC-03.00), preservando links dirigidos.

### 2.4. Persistencia y Debugging
- **Snapshot Service:** Exportación del Registry generado a JSON (embebido en payload) para auditoría y visualización del
  inventario bootstrapeado.
- **Loader de Referencias:** Lógica de búsqueda/validación de tags en Registry antes de procesar el grafo de red.

## 3. Entregables (Implementados)
- [x] **Project Loader (auto-instanciación):** scan → import → build() para boards + assemblies + network.
- [x] **Motor de Inferencia del Registry:** bootstrap en memoria desde Board DSL + assemblies.
- [x] **Validador de Integridad:** Network compiler con error inmediato si hay referencias inválidas.
- [x] **Especificación de Tags:** jerarquía de tags board/col/protection/terminal (terminales se habilitan más adelante).
- [x] **Adapter con Tests:** suite de pruebas para bootstrap + compile + adapter → ElecboardIR.
- [x] **Snapshot JSON:** registry snapshot y logical_ir embebidos en payload.

## 4. Criterios de Aceptación (Cumplidos)
- [x] El sistema genera un Registry completo sin archivos externos (solo Board DSL + assemblies declaradas).
- [x] Un error en el tag de una protección en Network detiene el proceso (error inmediato).
- [x] Tests unitarios demuestran transformación DSL→IR y preservan links dirigidos (`from` → `to`).

## 5. Notas de Diseño (Estado actual)
- Board DSL auto-expone:
  - **ENTRYPOINTS:** `main_protection()` (tag explicitado por el usuario en Network).
  - **ENDPOINTS:** `add_circuit()` y `add_sub_circuit()` (subcircuits namespaced como `G1:C1`).
- Network DSL se mantiene manual y explícita:
  - Por ahora se usa `.protection("<TAG>")` y no se automatiza el entrypoint.
- Terminales quedan habilitados para tableros de control en un sprint posterior.