# Esquema de factura

Usa UTF-8 y un objeto JSON por documento.

## Campos principales

- `schema_version`: entero, actualmente `1`.
- `status`: `draft`, `needs_review`, `approved`, `partially_applied`, `partially_applied_blocked`, `applied` o `no_stock_action`.
- `applied_to_inventory`: booleano.
- `document`: metadatos del DTE.
- `lines`: líneas comerciales.
- `checks`: reconciliaciones calculadas.
- `approval`: opcional; identifica quién aprobó, cuándo y qué versión.
- `application_log`: lista de movimientos realmente ejecutados.

## Documento

`document` contiene `type`, `supplier`, `folio`, `issue_date`, `source_images`, `invoice_total_clp` y `quantity_rule`. Agrega `reference_folio` y `reason` cuando sea una nota de crédito. Si los totales de línea impresos difieren del total documental únicamente por un redondeo menor, registra la diferencia en `rounding_difference_clp`; no la ocultes ni la asignes arbitrariamente a un producto.

## Línea

Cada línea contiene:

- `line_number` y `supplier_code`;
- `invoice_description` sin reinterpretar;
- `quantity_source` y `quantity_units`;
- `invoice_unit_cost_displayed_clp`, `invoice_line_total_clp` y `exact_unit_cost_from_line_clp`; este último es el costo bruto real por unidad de inventario, con impuestos y cargos logísticos incluidos, calculado como `invoice_line_total_clp / quantity_units` y conservado con dos decimales. El precio de compra aplicado en el sitio es este valor truncado al peso entero y debe figurar en el registro de aplicación;
- `stock_delta_units`;
- `inventory_match`, o `null` si no está resuelta;
- `ambiguities`, lista vacía cuando la línea está lista.

Una línea diferida conserva `quantity_units`, pero usa `stock_delta_units: 0` y registra `deferred: true`, `deferred_original_stock_delta_units` y `deferred_reason`. No se considera ambigua para el lote aprobado, pero debe aparecer claramente como excluida.

`inventory_match` conserva `name`, `barcode`, `format`, precios actuales, `current_stock`, `simulated_stock_after_receipt`, `confidence` y `evidence`.

## Estados

- `draft`: extracción incompleta o aún no contrastada.
- `needs_review`: validación terminada, pero existen decisiones para el usuario.
- `approved`: versión concreta aprobada y lista para aplicar.
- `partially_applied`: todas las líneas incluidas en el lote fueron aplicadas, pero permanecen una o más líneas diferidas con movimiento cero.
- `partially_applied_blocked`: parte del lote aprobado fue verificada, pero una o más líneas autorizadas no pudieron guardarse por un rechazo del sistema. Conserva el movimiento aprobado en la línea y registra el bloqueo y el stock sin cambio en `application_log`; nunca lo marques como diferido por el usuario.
- `applied`: todas las líneas autorizadas fueron verificadas después de cargarse.
- `no_stock_action`: documento clasificado y auditado que no representa movimiento físico, por ejemplo una nota de crédito por diferencia de precio.

No marques `approved` por inferencia y no marques `applied` hasta comprobar en el sitio el stock posterior de cada línea.

## Identidad y duplicados

La clave primaria humana es `supplier + document.type + folio`. Usa también fecha y total como controles. Dos fotografías con esa misma identidad deben consolidarse, no generar dos movimientos.
