#!/usr/bin/env python3
"""Inspect an Excel workbook before mapping it into the toolkit.

Point this at any spreadsheet (a community data dump, your own build
sheet, an exported wiki table) and it prints the shape of the data: sheet
sizes, header rows, value types, and -- most usefully -- **whether the
cells contain formulas**. A community sheet full of hard numbers is a
snapshot; a sheet with live formulas is the author's model, and the model
is what you actually want.

    python tools/inspect_workbook.py data/whatever.xlsx
    python tools/inspect_workbook.py data/whatever.xlsx --sheet Sheet3 --rows 30
    python tools/inspect_workbook.py data/whatever.xlsx --formulas
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path


def _load(path: Path, data_only: bool):
    from openpyxl import load_workbook

    return load_workbook(filename=str(path), data_only=data_only, read_only=False)


def summarise(path: Path, formulas: bool) -> None:
    wb = _load(path, data_only=not formulas)
    print(f"file      : {path}")
    print(f"sheets    : {len(wb.sheetnames)}")
    print(f"showing   : {'formulas' if formulas else 'cached values'}")
    print()

    for name in wb.sheetnames:
        ws = wb[name]
        rows = ws.max_row or 0
        cols = ws.max_column or 0
        merged = len(ws.merged_cells.ranges)
        non_empty = 0
        types: Counter[str] = Counter()
        formula_count = 0
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                non_empty += 1
                types[type(cell.value).__name__] += 1
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    formula_count += 1
        flag = "  <-- formulas!" if formula_count else ""
        print(f"[{name}]  {rows} rows x {cols} cols  "
              f"non-empty={non_empty}  merged={merged}  formulas={formula_count}{flag}")
        print(f"    types: {dict(types)}")


def preview(path: Path, sheet: str, n_rows: int, formulas: bool) -> None:
    wb = _load(path, data_only=not formulas)
    if sheet not in wb.sheetnames:
        raise SystemExit(f"no sheet {sheet!r}; available: {wb.sheetnames}")
    ws = wb[sheet]
    print(f"--- preview: {sheet} (first {n_rows} rows) ---")
    for i, row in enumerate(ws.iter_rows(max_row=n_rows), start=1):
        cells = []
        for cell in row:
            if cell.value is None:
                cells.append("·")
            else:
                text = str(cell.value)
                cells.append(text if len(text) <= 28 else text[:27] + "…")
        print(f"{i:>4} | " + " | ".join(cells))


def find_constants(path: Path, min_count: int = 2) -> None:
    """Numeric literals that repeat often are usually design constants."""
    wb = _load(path, data_only=not formulas_flag)
    counter: Counter[float] = Counter()
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                    counter[round(float(cell.value), 6)] += 1
    print(f"--- most repeated numeric values (candidates for design constants) ---")
    for value, count in counter.most_common(25):
        if count >= min_count:
            print(f"  {value:>14}  x{count}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("workbook", help="path to .xlsx / .xlsm")
    p.add_argument("--sheet", default=None, help="preview a specific sheet")
    p.add_argument("--rows", type=int, default=15)
    p.add_argument("--formulas", action="store_true",
                   help="show formula text instead of cached values")
    p.add_argument("--constants", action="store_true",
                   help="list the most repeated numbers across all sheets")
    args = p.parse_args()

    path = Path(args.workbook)
    if not path.exists():
        raise SystemExit(f"not found: {path}")

    formulas_flag = args.formulas
    summarise(path, args.formulas)
    if args.sheet:
        preview(path, args.sheet, args.rows, args.formulas)
    if args.constants:
        find_constants(path)
