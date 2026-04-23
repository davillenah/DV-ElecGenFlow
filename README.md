# ElecGenFlow

**ElecGenFlow** es un motor de diseño generativo (*Generative Design Engine*) **headless** para ingeniería eléctrica de Media Tensión (MT) y Baja Tensión (BT). Diseñado para proyectos industriales y comerciales que requieren trazabilidad total y automatización normativa.

---

## 💡 Arquitectura y Principios

El motor opera bajo una arquitectura de capas definida en el **ADR-0002**, donde la topología precede al cálculo:

- **Board DSL:** Define la anatomía del tablero (cargas, protecciones, buses, auxiliares).
- **Network DSL:** Define la conectividad mediante flujos dirigidos y enlaces explícitos.
- **Registry:** Única fuente de verdad para el etiquetado físico (TAGs) de componentes.
- **Top-down Aggregation:** La carga se declara en el extremo (Load) y se agrega hacia la fuente por topología, evitando duplicidad o protecciones huérfanas.

---

## 🛠 Alcance Técnico

- **Distribución:** Sistemas MT/BT, Tableros principales y seccionales.
- **Especialidades:** Iluminación técnica (LITE), HVAC industrial.
- **Renovables:** Plantas Fotovoltaicas (PV) y Sistemas de Almacenamiento (BESS).
- **Normativa (Default AR):** AEA 90364, AEA 95403, con respaldo IEC/IEEE.
- **Parámetros:** 50 Hz | 13.2 kV, 33 kV, 380/220 V.

---

## 📈 Estado del Proyecto

**Versión:** `v0.4.0`  
**Completado:** `EPIC-01` a `EPIC-04.00`  
**En curso:** `EPIC-04.01` (Agregación de cargas) y `EPIC-04.02` (Grafo DAG dirigido).

> [!NOTE]
> Según el Roadmap, la integración con **pandapower** (EPIC-07) y las reglas de validación **AEA** (EPIC-06) se ejecutan tras consolidar el modelo de componentes y el grafo lógico.

---

## 🚀 Quickstart (CLI)

### 1. Instalación
```bash
pip install -e .[dev]
```

### 2. Ejecución de Proyecto
```bash
python -m elecgenflow --project examples/fluent --out Reports
```

### 3. Artefactos Generados
Se exportan en `Reports/artifacts/`:
- `run_manifest.json`: Metadata de la ejecución.
- `engine_result.json`: Grafo resultante e IR del motor.

---

## 📂 Estructura del Proyecto

```text
Project/
├── project_owner.py         # Configuración global
└── Plant/
    ├── Boards/              # Definiciones Board DSL (*.py)
    ├── ccm_assembly.py      # Definición de ensamblajes de CCM
    └── network/
        └── electrical_network.py  # Conectividad Network DSL
```

---

## 🔌 Ejemplos de Network DSL

### Conexión entre Tableros (Fluent API)
```python
from electro_core.network import Network

def build(network: Network) -> Network:
    return (network
        .supply_from("TGBT-GENERAL")
        .column("COL-03")
        .protection("Q59")
        .to("TS-FUERZA")
        .protection("IG")
        .with_wire("W123")
        .done())
```

### Conexión a Carga Final
```python
def build(network: Network) -> Network:
    return (network
        .from_source("CCM-48")
        .column("COL-05")
        .protection("QM12")
        .with_wire("4x10mm2")
        .ends_at_load("MOTOR-BOMBA-01"))
```

---

## 📖 Documentación Interna
Consulte la carpeta `/docs` para detalles específicos:
- [Roadmap](./docs/ROADMAP.md)
- [ADRs](./docs/adr/)
- [Backlog](./docs/backlog/)
- [Specs](./docs/specs/)