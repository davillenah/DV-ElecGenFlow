# ESPECIFICACIÓN TÉCNICA: EPIC‑04.01 — Dimensionamiento y Marco Normativo (Post‑IR)

**Estado:** Planned  
**Release objetivo:** v0.4.1

---

## 1. OBJETO
EPIC‑04.01 define servicios de ingeniería (agregación de cargas, validación DAG, validación normativa y trazabilidad)
sobre el modelo lógico del sistema.

**Aclaración (post‑EPIC‑03.00):**  
EPIC‑04.01 **no rompe ni reemplaza** el Elecboard IR v1 entregado en EPIC‑03.00.  
Puede incorporar **referencias** (tags/wires/protections/terminals) vía `meta` y/o estructuras auxiliares en `DesignCandidate`,
manteniendo retrocompatibilidad.

---

## 1.1 ORDEN DE IMPLEMENTACIÓN (post‑EPIC‑03.00)
Este EPIC se implementará en el siguiente orden obligatorio:

1) **EPIC‑04.00:** Adaptar el motor para soportar la escritura por Board DSL + Network DSL (entrada canónica).  
2) **EPIC‑04.03:** Incorporar tablas nominales mínimas en **JSON** para comenzar pruebas (sin DB real).  
3) **EPIC‑04.04:** Implementar **validación normativa de lo seleccionado** (sin automatización/dimensionamiento).  
4) **EPIC‑04.XX:** Agregar catálogo de fabricantes/modelos en **JSON** (preparación para automatización futura).

**Nota:** En esta etapa **NO** se implementa Web ni DB oficial.

---

## 2. ALCANCE TÉCNICO
Se define la implementación de capacidades de ingeniería sobre el modelo lógico bajo los siguientes pilares:

- **Agregación de cargas (EPIC‑04.01):**
  - La carga se define en el nivel más bajo (circuitos/terminales).
  - Se agrega hacia arriba por topología dirigida.
  - Prohibido persistir cargas agregadas en niveles intermedios.

- **Topología dirigida (EPIC‑04.02):**
  - Interpretación de alimentación como grafo dirigido (DAG eléctrico).
  - Detección de ciclos eléctricos reales y nodos no alcanzables.

- **Tablas nominales (EPIC‑04.03):**
  - Tablas técnicas versionadas en **JSON** (cables, protecciones, métodos de instalación).
  - Uso inicial en modo “validación” para pruebas.

- **Validación (EPIC‑04.04):**
  - Validar decisiones manuales del usuario (ej. cable elegido, protección elegida).
  - Aún **sin** dimensionamiento automático (no propone ni optimiza).

- **Jerarquía normativa (EPIC‑04.05):**
  - Orden de prelación: Cliente → AEA/IRAM → IEC/IEEE (fallback trazable).

- **Reportes/alertas (EPIC‑04.06):**
  - Advertencias y violaciones trazables (modo no bloqueante por defecto).

---

## 3. EXCLUSIONES Y RESTRICCIONES (CORREGIDO)
### 3.1 Se prohíbe
- Reemplazar o invalidar el Elecboard IR v1 (EPIC‑03.00).
- Persistir **cargas agregadas** en nodos/tableros (duplicación de datos).
- Asumir datos eléctricos críticos “a ojo” sin origen declarado en Registry/Tablas/DSL.

### 3.2 Fuera de alcance por ahora (fase inicial)
- Implementación web (Flask u otras).
- Base de datos oficial (PostgreSQL u otras como system-of-record).
- Dimensionamiento automático (propuesta/selección automática de cable/protección).
- Optimización heurística (se reserva para EPIC‑05+ y EPIC‑09).

### 3.3 Se permite
- Enriquecer por **referencias** (IDs/tags) y producir contextos transitorios:
  - CableContext / LinkContext
  - Reportes técnicos (warnings/violations)
- Validación normativa de lo **seleccionado por el usuario** (sin automatizar).

---

## 4. ROL ARQUITECTÓNICO (CORREGIDO)
El sistema se organiza por capas sin mezclar responsabilidades:

- **EPIC‑03.00 (Estructura / IR lógico):** describe *qué existe* (entidades y topología estructural).
- **EPIC‑04.00 (Entrada canónica):** define *cómo se declara* el proyecto (Board DSL + Network DSL + Registry).
- **EPIC‑04.01–04.06 (Ingeniería / Evaluación):** evalúa *qué cumple* bajo reglas y normativa, y explica el resultado.
- **EPIC‑05.00 (Automatización):** usará los mismos validadores para proponer soluciones automáticas en el futuro.

---

## 5. ENTIDADES PRINCIPALES (SERVICIOS Y ESTRUCTURAS)
1) **LoadSummary**
   - Potencia instalada / demanda / simultaneidad por nodo y tablero.

2) **DirectedElectricalGraph**
   - DAG eléctrico de alimentación, ciclos eléctricos, alcanzabilidad.

3) **CableContext**
   - Estructura transitoria que vincula:
     - wire_id (o cable tag)
     - protección upstream (tag)
     - destino (board/terminal tag)
   - **No almacena** carga ni corriente como fuente de verdad; solo contexto derivado.

4) **NormativeTrace**
   - Evidencia: norma aplicada, nivel jerárquico, motivo del fallback.

5) **EngineeringReport**
   - Resultado con advertencias, violaciones, sugerencias y trazabilidad.
   - Por defecto no bloqueante (configurable).

---

## 6. REGLAS ESTRUCTURALES E INVARIANTES
- **Principio de sumatoria:** carga superior = suma estricta de cargas inferiores.
- **Unicidad de datos:** prohibido guardar cargas agregadas “arriba”.
- **Separación de responsabilidades:**
  - El cable conecta.
  - La protección protege al conductor.
  - La carga reside en el extremo inferior.
- **Validación pasiva:** reporta pero no frena salvo configuración explícita.

---

## 7. INTEGRACIÓN CON EL DOMAIN CORE
Servicios esperados:
- LoadAggregationService (abajo → arriba)
- DirectedGraphService (DAG eléctrico)
- CableContextResolver (wire + protección + destino)
- NormativeResolver (trazabilidad)

Los resultados se adjuntan al `DesignCandidate` como artifacts/report, sin mutar el IR base.

---

## 8. ESTRATEGIA DE DATOS (JSON → Local DB → DB oficial)
- **Fase 1 (prototipo):** JSON versionado (tablas nominales + catálogos).
- **Fase 2 (local, más adelante):** DB embebida para consultas/análisis.
  - Recomendación: **DuckDB** para analítica y agregaciones; **SQLite** como alternativa para persistencia simple.
- **Fase 3 (oficial, mucho más adelante):** **PostgreSQL**.
- **Fase 4 (muy futuro):** posible migración con Flask. No es parte del alcance actual.

---

## 9. ENTREGABLES EXIGIBLES
1) Servicios de agregación de cargas y validación DAG.
2) Esquemas JSON versionados de tablas nominales.
3) Motor de validación (sin automatización) de:
   - coherencia cable vs protección vs carga downstream
4) Motor de resolución normativa con fallback trazable.
5) Generador de reportes técnicos auditables.

---

## 10. CRITERIOS DE ACEPTACIÓN Y CIERRE
EPIC‑04.01 se considera aceptada cuando:
- La propagación de cargas funciona en grafos complejos sin duplicación.
- Se detectan ciclos eléctricos y nodos no alcanzables.
- Las validaciones generan evidencia normativa trazable sin bloquear por defecto.
- Se preserva compatibilidad con EPIC‑03.00.

---

## 11. NOTA DE DISEÑO
Se prioriza la trazabilidad y auditabilidad por sobre la automatización.
El sistema debe poder responder explícitamente:
**“¿Por qué esto NO cumple y bajo qué norma?”**
