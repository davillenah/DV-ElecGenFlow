# ElecGenFlow

**ElecGenFlow** es un *Generative Design Engine* **headless** para ingeniería eléctrica de **Media Tensión (MT)** y **Baja Tensión (BT)**, enfocado en aplicaciones industriales y comerciales.

## Principio rector

- Board DSL describe qué es cada tablero (cargas abajo, protecciones internas, buses, auxiliares).
- Network DSL describe cómo se conectan tableros (supply_from → to → wire).
- Registry/DB es la única fuente de verdad para tags físicos (boards, columnas, protecciones, borneras, cables).
- El IR del motor debe poder construirse desde esas capas sin duplicar cargas ni “inventar” protecciones en cables.
- La carga se declara abajo y se agrega hacia arriba por topología dirigida.

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

**Frecuencia:** 50 Hz  
**Tensiones típicas:** 13.2 kV, 33 kV, 380/220 V

## Estado del proyecto
Versión actual: **v0.4.0**  
EPICs completadas: **EPIC-01, EPIC-02, EPIC-03, EPIC-04.00**  
Próxima etapa: **EPIC-04.01 / EPIC-04.02**

> **Nota:** Siguiendo la arquitectura de capas definida en el **ADR-0002**, la simulación real con **pandapower** y las reglas normativas **AEA** se implementan en las **EPIC-07** y **EPIC-06** respectivamente, garantizando la previa existencia del modelo de componentes y el grafo lógico.

---

Para más detalles, consulte la carpeta DOCS:
- [Roadmap](./docs/ROADMAP.md)
- [ADRs](./docs/adr/)
- [Backlog](./docs/backlog/)
- [Epics](./docs/epics/)
- [Specs](./docs/specs/)