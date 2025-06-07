#!/usr/bin/env python3
"""Exportar costo diario de trazas a archivos CSV."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("data/traces.db")
REPORTS_DIR = Path("data/reports")


def export_daily_cost(db_path: Path = DB_PATH, reports_dir: Path = REPORTS_DIR) -> None:
    """Genera un archivo CSV por cada fecha con la suma del costo."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    reports_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT DATE(timestamp) AS day, SUM(COALESCE(cost_usd, 0))
            FROM llm_traces
            GROUP BY DATE(timestamp)
            ORDER BY day
            """
        ).fetchall()

    for day, total in rows:
        out_file = reports_dir / f"{day}.csv"
        with out_file.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["date", "cost_usd"])
            writer.writerow([day, f"{float(total):.6f}"])

    print(f"Generated {len(rows)} report files in {reports_dir}")


if __name__ == "__main__":
    export_daily_cost()
