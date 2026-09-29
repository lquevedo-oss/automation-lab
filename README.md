# Automation Lab

Ejemplos ejecutables de automatización, inteligencia competitiva, analítica comercial y control documental. Funcionan sin credenciales, sin dependencias externas y sin escribir en sistemas reales.

## Probar

Requiere Python 3.12 o superior.

```bash
python demo.py
python -m lab.invoice_validation examples/invoice.json
python -m unittest discover -s tests -v
```

## Proyectos representados

| Ejemplo | Problema que ilustra |
|---|---|
| Inteligencia competitiva | Evidencia verificable, deduplicación y acciones vinculadas a hallazgos. |
| Funnel de engagement | Asociar consumo de contenido con negocios sin confundir asociación con causalidad. |
| Oportunidades perdidas | Priorizar recuperación y dejar causas desconocidas para revisión humana. |
| Calendario | Respetar capacidad por fecha y país y sugerir alternativas. |
| Migración de información | Detectar registros faltantes, duplicados y cambios. |
| Versionado documental | Detectar diferencias y bloquear revisiones repetidas mediante hash. |
| Datos a presentaciones | Preparar una estructura de tarjetas desde datos tabulares. |
| Facturas e inventario | Reconciliar cantidades, movimientos, totales y aprobación antes de una carga. |

## Alcance y procedencia

Este repositorio contiene demostraciones genéricas preparadas para el portafolio de Luka. Los ejemplos ilustran problemas trabajados en proyectos reales, pero no son copias de los sistemas productivos ni contienen reglas, prompts o esquemas privados de una empresa.

El validador de facturas se adaptó de una utilidad local reutilizable; se excluyeron todos los documentos, equivalencias de proveedores, catálogos y registros originales. Los otros módulos se reconstruyeron como ejemplos independientes con datos ficticios. Las cifras y políticas de priorización son inventadas.

Las integraciones originales incluyeron Apps Script, HubSpot, Sheets, Looker Studio, BigQuery, Figma y n8n. Esta edición pública no se conecta a esas cuentas. En particular, el ejemplo documental no implementa un ejecutor autónomo de Figma ni afirma que ese pendiente del piloto original esté resuelto.

## Diseño

- Funciones puras para revisar reglas y resultados antes de integrar sistemas.
- `Decimal` para cálculos monetarios del ejemplo.
- Evidencia y resultados reproducibles; clasificación desconocida permanece pendiente.
- Aprobación humana explícita antes de una aplicación de inventario o publicación documental.
- Datasets sintéticos en `examples/`; no incluyen información de clientes o proveedores.

Desarrollo y documentación con asistencia de IA. [Ver el portafolio y los casos](https://github.com/lquevedo-oss/portfolio).
