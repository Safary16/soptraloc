"""Utilidades compartidas para importar planillas operativas de forma tolerante."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable

import pandas as pd


def normalize_label(value) -> str:
    """Normaliza encabezados sin depender de mayúsculas, tildes o espacios."""
    text = '' if value is None else str(value)
    text = text.replace('\xa0', ' ').strip().lower()
    text = ''.join(
        char for char in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(char)
    )
    text = re.sub(r'[_\-]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def normalize_columns(df: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    """Renombra columnas y falla si dos encabezados terminan en el mismo campo."""
    normalized_aliases = {normalize_label(k): v for k, v in aliases.items()}
    renamed = [normalized_aliases.get(normalize_label(col), normalize_label(col).replace(' ', '_')) for col in df.columns]
    duplicates = sorted({name for name in renamed if renamed.count(name) > 1})
    if duplicates:
        raise ValueError(f"Columnas duplicadas después de normalizar: {', '.join(duplicates)}")
    result = df.copy()
    result.columns = renamed
    return result


def read_excel_with_header_detection(path: str | Path, expected_aliases: Iterable[str], max_header_rows: int = 10) -> pd.DataFrame:
    """Detecta la fila de encabezado buscando nombres conocidos en las primeras filas."""
    preview = pd.read_excel(path, header=None, nrows=max_header_rows)
    expected = {normalize_label(v) for v in expected_aliases}
    best_row, best_score = 0, -1
    for index, row in preview.iterrows():
        labels = {normalize_label(v) for v in row.tolist() if pd.notna(v)}
        score = len(labels & expected)
        if score > best_score:
            best_row, best_score = int(index), score
    if best_score <= 0:
        best_row = 0
    return pd.read_excel(path, header=best_row)


def clean_cell(value, default=None):
    if pd.isna(value):
        return default
    text = str(value).replace('\xa0', ' ').strip()
    return text if text else default
