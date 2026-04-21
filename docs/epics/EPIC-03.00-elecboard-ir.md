# ESPECIFICACIÓN TÉCNICA: EPIC‑03.00 — Elecboard IR v1 (Logical Model)

**Estado:** Planned  
**Release objetivo:** v0.3.0

## 1. OBJETO
Se establece la definición del **Elecboard IR (Intermediate Representation)** como el modelo lógico, estructural y explícito del sistema eléctrico. Esta representación debe ser independiente de cálculos, magnitudes físicas y motores de simulación, constituyéndose como la primera formalización de la red eléctrica dentro del marco de *ElecGenFlow*.

## 2. ALCANCE TÉCNICO
Se limita el alcance de la EPIC‑03.00 exclusivamente a la definición del modelo lógico. Se debe incluir de manera obligatoria:

*   **Representación de entidades:** Tableros eléctricos (*boards*), nodos (barras, puntos de conexión), ramas lógicas (conexiones, *feeders*), cargas abstractas y fuentes abstractas.
*   **Estructura de grafo:** Se define la arquitectura de red mediante grafos.
*   **Validaciones estructurales:** Se exige la verificación de conectividad, coherencia de fases y topología (radial o mallada declarativa).
*   **Serialización:** Se requiere la implementación de mecanismos de validación y persistencia del IR.

**Restricciones de exclusión:** No se permite la inclusión de parámetros eléctricos reales, simulaciones, ni la aplicación de normativas físicas en esta etapa.

## 3. EXCLUSIONES (FUERA DE ALCANCE)
Se prohíbe explícitamente la integración de los siguientes elementos en la EPIC‑03.00:
*   Cálculo de magnitudes (corrientes, tensiones, potencias).
*   Parámetros físicos de conductores y ampacidades.
*   Aplicación de reglas AEA / IEC.
*   Integración con *pandapower* o selección de componentes comerciales.

Dichos elementos se reservan para fases de desarrollo posteriores.

## 4. ROL ARQUITECTÓNICO
El Elecboard IR se constituye como la "verdad estructural" del sistema. Se establece su relación jerárquica con el resto de las especificaciones:
*   **EPIC‑02.00:** Provee los contratos generales.
*   **EPIC‑03.00:** Define la estructura lógica base.
*   **EPIC‑04.00 y EPIC-05.00:** Enriquecen el IR con componentes y magnitudes.
*   **EPIC‑07.00 y EPIC-08.00+:** Gestionan la traducción a motores de cálculo y optimización.

## 5. ENTIDADES PRINCIPALES Y CAMPOS OBLIGATORIOS
Se define la estructura mínima para los siguientes objetos:

1.  **Board (Tablero):** Se requiere `board_id`, `name`, `level` (MT/BT), `phases`, `nodes` y `meta`.
2.  **Node (Nodo):** Se requiere `node_id`, `board_id`, `phases`, `kind` (bus, junction, terminal) y `meta`.
3.  **Branch (Rama):** Se requiere `branch_id`, `from_node`, `to_node`, `kind`, `phases` y `meta`.
4.  **Load (Carga):** Se requiere `load_id`, `node_id`, `kind`, `phases` y `meta`.
5.  **Source (Fuente):** Se requiere `source_id`, `node_id`, `kind`, `phases` y `meta`.

## 6. REGLAS ESTRUCTURALES E INVARIANTES
Se debe garantizar el cumplimiento de las siguientes condiciones de integridad:
*   Toda carga se asociará obligatoriamente a un nodo.
*   Toda rama conectará exactamente dos nodos válidos.
*   Se prohíbe la existencia de nodos huérfanos sin conexión.
*   Se exige compatibilidad técnica entre las fases de ramas y nodos.
*   Se debe declarar explícitamente la conectividad de la red o la existencia de islas.

## 7. INTEGRACIÓN CON EL DOMAIN CORE
El Elecboard IR se transportará dentro del atributo `DesignCandidate.logical_ir`. Se establece que el *Domain Core* no interpretará el contenido del IR, limitándose exclusivamente a su validación estructural.

## 8. ENTREGABLES EXIGIBLES
Para la conclusión de la EPIC‑03.00, se requiere la entrega de:
1.  Modelos Pydantic del Elecboard IR.
2.  Módulos de validación estructural.
3.  Protocolos de tests unitarios.
4.  Documentación técnica del modelo lógico e integración con `DesignCandidate`.

## 9. CRITERIOS DE ACEPTACIÓN Y CIERRE
La EPIC‑03.00 se considerará finalizada únicamente cuando:
*   Se verifique la existencia de un IR lógico funcional y completo.
*   Se valide la capacidad de serialización y deserialización del modelo.
*   Se demuestre la ausencia de dependencias con componentes físicos o motores de simulación.

## 10. NOTA DE DISEÑO
Se define el Elecboard IR como una representación previa, estable y extensible, análoga a un Árbol de Sintaxis Abstracta (AST), evitando su confusión con modelos de ejecución final como *pandapower*.