# PRODUCT BACKLOG — elecgenflow

> Nota:
> Los entregables detallados solo se listan para EPICs completadas
> o activamente en desarrollo. Las EPICs futuras se describen a nivel
> de objetivos hasta que entren en ejecución.

## EPIC-1 — Scaffolding profesional + gobernanza
- Prioridad: Alta
- Estado: Hecho
- Release: v0.1.0

## EPIC-2 — Núcleo de dominio (DDD) y contratos del motor
- Prioridad: Muy Alta
- Estado: Hecho
- Release: v0.2.0
- Entregables:
  - Contratos pydantic (DesignProblem, Candidate, Constraints, Objectives, Metrics, Rules, Artifacts, Result)
  - Config loader YAML + defaults AR
  - RunManifest reproducible
  - Engine headless stub + CLI mínimo
  - Tests unitarios base + CI

## EPIC-3 — Elecboard IR v1 (modelo lógico)
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.3.0

## EPIC-4 — Component Library & Part Management
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.4.0
- Objetivo: Base de datos de componentes comerciales (cables, protecciones, transformadores) con parámetros técnicos predefinidos.

## EPIC-5 — Modelo eléctrico real (líneas y cargas)
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.5.0

## EPIC-6 — Rule & Constraint Engine (AEA/IEC)
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.6.0

## EPIC-7 — Simulation Engine (pandapower) + métricas
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.7.0

## EPIC-8 — Generador de variantes
- Prioridad: Media
- Estado: Pendiente
- Release: v0.8.0

## EPIC-9 — Optimizador + Cost Model
- Prioridad: Media
- Estado: Pendiente
- Release: v0.9.0

## EPIC-10 — Scenario Manager (Snapshot & Comparison)
- Prioridad: Media
- Estado: Pendiente
- Release: v0.10.0
- Objetivo: Persistencia y comparación técnica entre diferentes variantes y estados de red.

## EPIC-11 — Reporting & Exporting Engine (PDF/Excel/JSON)
- Prioridad: Media
- Estado: Pendiente
- Release: v0.11.0
- Objetivo: Generación automatizada de reportes de ingeniería y exportación de datos brutos.

## EPIC-12 — Calidad de energía (THD/PF)
- Prioridad: Media
- Estado: Pendiente
- Release: v0.12.0

## EPIC-13 — Protection Coordination & Tripping Curves
- Prioridad: Alta
- Estado: Pendiente
- Release: v0.13.0
- Objetivo: Estudio de selectividad y curvas de disparo para interruptores.

## EPIC-14 — PV/BESS
- Prioridad: Baja
- Estado: Pendiente
- Release: v0.14.0

## EPIC-15 — Industrial Hardening
- Prioridad: Media
- Estado: Pendiente
- Release: v0.15.0

## EPIC-16 — Release Candidate + docs finales
- Prioridad: Alta
- Estado: Pendiente
- Release: v1.0.0

## EPIC-17 — Integration Layer (IFC/DXF/JSON)
- Prioridad: Baja
- Estado: Pendiente
- Release: v1.1.0

## EPIC-18 — RBAC (Role-Based Access Control) & Audit Logs
- Prioridad: Baja
- Estado: Pendiente
- Release: v1.2.0