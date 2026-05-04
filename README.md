# ElecGenFlow

**ElecGenFlow** es un motor de diseño generativo (*Generative Design Engine*) **headless** para ingeniería eléctrica de Media Tensión (MT) y Baja Tensión (BT). Diseñado para proyectos industriales, comerciales y residenciales que requieren trazabilidad total y automatización normativa.

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
- **Especialidades:** Iluminación (LITE), Distribucion de Potencia (POWR), Climatizacion (HVAC).
- **Renovables:** Plantas Fotovoltaicas (PV) y Sistemas de Almacenamiento (BESS).
- **Normativa (Default AR):** AEA 90364, AEA 95403, con respaldo IEC/IEEE.
- **Parámetros:** 50 Hz | 13.2 kV, 33 kV, 380/220 V.

---

## 📈 Estado del Proyecto

**Versión:** `v0.4.3`  
**Completado:** `EPIC-01` a `EPIC-04.03`  
**En curso / extendido:** `EPIC-04.04` (validación Ib vs Iz + auto-sugerencia de sección + Cable Schedule)  
**Reporting:** `EPIC-11 precursor` (PDF desde artifacts) mejorado con secciones técnicas.

> [!NOTE]
> El dimensionamiento automático actual es **sugerido** (selección mínima por ampacidad que cumple) y se reporta como artifacts reproducibles.
> La coordinación completa Ib/In/Iz, derating completo (k_group/k_temp/k_soil) y caída de tensión quedan para próximos EPICs.


---

## 🚀 Quickstart (CLI)

### 1. Instalación
```bash
pip install -e .[dev]
```

### 2. Ejecución de Proyecto
```bash
python -m elecgenflow --project examples/Ford_BsAs_Pacheco
```

### 3. Artefactos Generados
Se exportan bajo Reports/<run_id>/artifacts/ dentro del proyecto:

- Reports/<run_id>/artifacts/load_report.json + .md
- Reports/<run_id>/artifacts/dag_report.json + .md
- Reports/<run_id>/artifacts/nominal_snapshot.json + .md
- Reports/<run_id>/artifacts/nominal_overlay_diff.json + .md
- Reports/<run_id>/artifacts/sizing_report.json + .md
- Reports/<run_id>/artifacts/cable_schedule.json + .md
- Reports/<run_id>/artifacts/selected_wires.json
- Reports/<run_id>/artifacts/engineering_report.pdf

---

## 📂 Estructura del Proyecto

```text
<Project>/
├── project_owner.py
├── Boards/
├── Networks/
└── Reports/
    └── <run_id>/
        └── artifacts/
```

---

## 🔌 Ejemplos de Network DSL

### Conexión entre Tableros (Fluent API)
```python
from electro_core.network import Network

def build(network: Network) -> Network:
    return ((
        networw
            .supply_from("TGBT_GENERAL")
                .column("COL-03")
                .protection("Q59")
            .to("TS_LITE_01")
                .protection("IG")
                .with_wire_id("W378")
                    .configured_as()
                        .multipolar()
                        .with_protection_cable_included()
                        .insulation("PVC")
                        .conductor("AL")
                        .installed_in("E")
                        .circuits(parallel=1, grouped=1)
        .done()
    ))
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









--- borrar todo desde aqui..

pip install -e .[dev]

black src tests 

black --check src tests 

ruff check src tests --fix 

ruff check src tests 

pytest 

mypy src 

python -m elecgenflow --project examples/Ford_BsAs_Pacheco