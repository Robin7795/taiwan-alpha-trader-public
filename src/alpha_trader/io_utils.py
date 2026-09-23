from __future__ import annotations
from pathlib import Path
from typing import Iterable
import pandas as pd
from pandas.errors import EmptyDataError, ParserError


def safe_read_csv(path: str | Path, *, dtype=None, expected_columns: Iterable[str] | None = None) -> pd.DataFrame:
    """Read a CSV without crashing on missing, zero-byte, header-only, or malformed-empty files.

    This is intentionally conservative: parse errors return an empty frame so the dashboard can
    continue rendering and surface a clear 'no data yet' state instead of a red traceback.
    """
    p = Path(path)
    cols = list(expected_columns or [])
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame(columns=cols)
    try:
        df = pd.read_csv(p, dtype=dtype)
    except (EmptyDataError, ParserError, UnicodeDecodeError):
        return pd.DataFrame(columns=cols)
    if df is None:
        return pd.DataFrame(columns=cols)
    if cols:
        for c in cols:
            if c not in df.columns:
                df[c] = pd.Series(dtype='object')
    return df


def write_csv_with_columns(df: pd.DataFrame | None, path: str | Path, columns: Iterable[str]) -> None:
    """Always write a parseable CSV, including headers when there are zero rows."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cols = list(columns)
    if df is None or df.empty:
        pd.DataFrame(columns=cols).to_csv(p, index=False, encoding='utf-8-sig')
        return
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA
    ordered = cols + [c for c in out.columns if c not in cols]
    out[ordered].to_csv(p, index=False, encoding='utf-8-sig')
