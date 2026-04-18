# ElecGenFlow

**ElecGenFlow** es un *Generative Design Engine* **headless** para ingeniería eléctrica de **Media Tensión (MT)** y **Baja Tensión (BT)**, enfocado en aplicaciones industriales y comerciales.

## Alcance
- Distribución eléctrica MT/BT
- Tableros eléctricos
- Iluminación técnica (LITE)
- HVAC industrial
- Plantas FV (PV) y sistemas BESS
- Calidad de energía y eficiencia energética

## Normativa (por defecto AR)
- AEA 90364
- AEA 95403
- IEC / IEEE (respaldo)

Frecuencia: 50 Hz  
Tensiones típicas: 13.2 kV, 33 kV, 380/220 V

## Estado del proyecto
Versión actual: **v0.2.0**  
EPIC completadas: EPIC-0, EPIC-1

EPIC-1 incluye:
- Contratos de dominio (pydantic) + validación
- Engine headless (orquestación stub) + manifest reproducible
- CLI mínimo para validar/ejecutar stub
- CI con ruff/black/mypy/pytest

> Nota: simulación real con pandapower y reglas AEA se implementan en EPIC-4/EPIC-5.
