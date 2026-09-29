#!/usr/bin/env python3
"""Validate an extracted invoice JSON without modifying external systems."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


ALLOWED_STATUSES = {"draft", "needs_review", "approved", "partially_applied", "partially_applied_blocked", "applied", "no_stock_action"}


def number(value, label, errors):
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError, TypeError):
        errors.append(f"{label} no es numérico: {value!r}")
        return Decimal(0)


def validate(data):
    errors = []
    warnings = []

    if data.get("schema_version") != 1:
        errors.append("schema_version debe ser 1")

    status = data.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"status inválido: {status!r}")

    document = data.get("document") or {}
    for field in ("type", "supplier", "folio", "issue_date", "source_images"):
        if not document.get(field):
            errors.append(f"falta document.{field}")

    lines = data.get("lines")
    if not isinstance(lines, list) or not lines:
        errors.append("lines debe contener al menos una línea")
        lines = []

    seen_line_numbers = set()
    sum_qty = Decimal(0)
    sum_totals = Decimal(0)
    unresolved = 0
    deferred_count = 0

    for index, line in enumerate(lines, start=1):
        prefix = f"lines[{index}]"
        line_number = line.get("line_number")
        if line_number in seen_line_numbers:
            errors.append(f"{prefix}.line_number duplicado: {line_number}")
        seen_line_numbers.add(line_number)

        if not line.get("invoice_description"):
            errors.append(f"{prefix}.invoice_description está vacío")

        quantity = number(line.get("quantity_units"), f"{prefix}.quantity_units", errors)
        delta = number(line.get("stock_delta_units"), f"{prefix}.stock_delta_units", errors)
        line_total = number(line.get("invoice_line_total_clp"), f"{prefix}.invoice_line_total_clp", errors)
        sum_qty += quantity
        sum_totals += line_total

        match = line.get("inventory_match")
        ambiguities = line.get("ambiguities") or []
        deferred = bool(line.get("deferred"))
        if deferred:
            deferred_count += 1
            if delta != 0:
                errors.append(f"{prefix}: una línea diferida debe tener stock_delta_units igual a cero")
            original_delta = number(
                line.get("deferred_original_stock_delta_units"),
                f"{prefix}.deferred_original_stock_delta_units",
                errors,
            )
            if original_delta == 0:
                errors.append(f"{prefix}: una línea diferida debe conservar el movimiento original")
            if not line.get("deferred_reason"):
                errors.append(f"{prefix}.deferred_reason está vacío")
        elif not match or ambiguities:
            unresolved += 1

        if match:
            for field in ("name", "barcode", "format", "current_stock", "simulated_stock_after_receipt", "confidence"):
                if match.get(field) in (None, ""):
                    errors.append(f"{prefix}.inventory_match.{field} está vacío")
            current = number(match.get("current_stock"), f"{prefix}.inventory_match.current_stock", errors)
            simulated = number(match.get("simulated_stock_after_receipt"), f"{prefix}.inventory_match.simulated_stock_after_receipt", errors)
            if simulated != current + delta:
                errors.append(f"{prefix}: stock simulado no equivale a stock actual + movimiento")

    document_total = number(document.get("invoice_total_clp"), "document.invoice_total_clp", errors)
    rounding_difference = number(
        document.get("rounding_difference_clp", 0),
        "document.rounding_difference_clp",
        errors,
    )
    if rounding_difference and abs(rounding_difference) > Decimal(5):
        errors.append("document.rounding_difference_clp excede el máximo auditable de $5")
    if sum_totals + rounding_difference != document_total:
        errors.append(
            f"suma de líneas {sum_totals} más diferencia de redondeo "
            f"{rounding_difference} no coincide con total documental {document_total}"
        )
    elif rounding_difference:
        warnings.append(
            f"se aceptó una diferencia de redondeo documentada de {rounding_difference} CLP"
        )

    applied = bool(data.get("applied_to_inventory"))
    applied_statuses = {"partially_applied", "partially_applied_blocked", "applied"}
    if (status in applied_statuses) != applied:
        errors.append("status aplicado y applied_to_inventory deben coincidir")
    if status in {"approved", *applied_statuses} and unresolved:
        errors.append("una factura aprobada o aplicada no puede tener líneas sin resolver")
    if status in {"approved", *applied_statuses} and not data.get("approval"):
        errors.append("una factura aprobada o aplicada requiere approval")
    if status in applied_statuses and not data.get("application_log"):
        errors.append("una factura aplicada total o parcialmente requiere application_log")
    if status == "partially_applied" and not deferred_count:
        errors.append("partially_applied requiere al menos una línea diferida")
    if status == "applied" and deferred_count:
        errors.append("applied no permite líneas diferidas")
    if status == "partially_applied_blocked" and not any(
        entry.get("status") == "blocked_no_movement" for entry in data.get("application_log", [])
    ):
        errors.append("partially_applied_blocked requiere una línea bloqueada en application_log")

    declared_checks = data.get("checks") or {}
    if declared_checks.get("total_quantity_units") not in (None, int(sum_qty)):
        warnings.append("checks.total_quantity_units no coincide con las líneas")
    if declared_checks.get("sum_of_line_totals_clp") not in (None, int(sum_totals)):
        warnings.append("checks.sum_of_line_totals_clp no coincide con las líneas")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "folio": document.get("folio"),
            "line_count": len(lines),
            "total_quantity_units": int(sum_qty),
            "sum_of_line_totals_clp": int(sum_totals),
            "unresolved_lines": unresolved,
            "deferred_lines": deferred_count,
            "status": status,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("invoice", type=Path)
    args = parser.parse_args()
    with args.invoice.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    result = validate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
