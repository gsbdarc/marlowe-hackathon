"""Stage 1a: read the SEC header of each 10-K-family original and each 8-K filed in one year.

Writes data/interim/headers/headers_<year>.parquet. Amendments are not read (Stage 1
drops them); 10-Qs need only their filing date, which the index already has.

Run as a Slurm array with one task per filing year (slurm/01_headers.slurm), or
directly: python scripts/01_headers.py --year 2008 [--limit 200].
"""

import argparse
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
OUT_DIR = INTERIM / "headers"

HEADER_END = b"</SEC-HEADER>"
CHUNK = 64 * 1024
MAX_HEADER = 4 * 1024 * 1024  # some multi-filer headers are long

TOP_FIELDS = {
    "ACCESSION NUMBER": "hdr_accession",
    "CONFORMED SUBMISSION TYPE": "hdr_form_type",
    "PUBLIC DOCUMENT COUNT": "doc_count",
    "CONFORMED PERIOD OF REPORT": "period_of_report",
    "FILED AS OF DATE": "filed_as_of",
}
FILER_FIELDS = {
    "COMPANY CONFORMED NAME": "hdr_company_name",
    "CENTRAL INDEX KEY": "hdr_cik",
    "STANDARD INDUSTRIAL CLASSIFICATION": "sic_raw",
    "STATE OF INCORPORATION": "state_of_inc",
    "FISCAL YEAR END": "fiscal_year_end",
}
LINE = re.compile(r"^\s*([A-Z][A-Z0-9 ,&/()-]*?):\s*(.*?)\s*$")
SIC = re.compile(r"\[(\d{3,4})\]\s*$")


def read_header(path):
    """Return the header text, or raise if it can't be found."""
    buf = b""
    with open(path, "rb") as f:
        while len(buf) < MAX_HEADER:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            buf += chunk
            end = buf.find(HEADER_END)
            if end >= 0:
                return buf[:end].decode("latin-1")
    raise ValueError("no </SEC-HEADER>")


def parse_header(text, index_cik):
    """Top-level fields, 8-K items, and the FILER block that matches the index CIK."""
    rec = {"item_info": []}
    filers, current, in_filer = [], None, False
    for line in text.splitlines():
        m = LINE.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        indented = line[:1] in ("\t", " ")
        if not indented:
            in_filer = key in ("FILER", "FILED BY", "SUBJECT COMPANY", "REPORTING-OWNER")
            if key == "FILER":
                current = {}
                filers.append(current)
            elif key == "ITEM INFORMATION":
                rec["item_info"].append(val)
            elif key in TOP_FIELDS:
                rec[TOP_FIELDS[key]] = val
        elif in_filer and current is not None and key in FILER_FIELDS:
            current.setdefault(FILER_FIELDS[key], val)

    chosen = next((f for f in filers if _int(f.get("hdr_cik")) == index_cik), filers[0] if filers else {})
    rec.update(chosen)
    rec["n_filers"] = len(filers)
    sic = SIC.search(rec.pop("sic_raw", "") or "")
    rec["sic"] = int(sic.group(1)) if sic else None
    return rec


def _int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def process(row):
    out = {"accession": row.accession, "cik": row.cik, "status": "ok", "error": None}
    try:
        out["file_bytes"] = os.path.getsize(row.filepath)
        out.update(parse_header(read_header(row.filepath), row.cik))
    except FileNotFoundError:
        out.update(status="missing", error="file not found")
    except Exception as e:  # recorded per filing, reported by year
        out.update(status="header_error", error=f"{type(e).__name__}: {e}"[:300])
    return out


def load_index(year):
    k = pd.read_parquet(INTERIM / "edgar_index_10k.parquet")
    k = k[(k.year == year) & ~k.form_type.str.endswith("/A")]
    e = pd.read_parquet(INTERIM / "edgar_index_8k.parquet")
    e = e[e.year == year]
    return pd.concat([k, e], ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=None, help="filing year; defaults to the Slurm array task ID")
    ap.add_argument("--threads", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 8)) * 4)
    ap.add_argument("--limit", type=int, default=None, help="read only this many filings (testing)")
    args = ap.parse_args()
    year = args.year if args.year is not None else int(os.environ["SLURM_ARRAY_TASK_ID"])

    idx = load_index(year)
    if args.limit:
        idx = idx.sample(min(args.limit, len(idx)), random_state=0)
    t0 = time.time()
    with ThreadPoolExecutor(args.threads) as pool:
        recs = list(pool.map(process, idx.itertuples(index=False), chunksize=64))
    hdr = pd.DataFrame(recs)
    df = idx.merge(hdr, on=["accession", "cik"], how="left", validate="one_to_one")
    for c in ("period_of_report", "filed_as_of"):
        df[c] = pd.to_datetime(df[c], format="%Y%m%d", errors="coerce")
    df["doc_count"] = pd.to_numeric(df["doc_count"], errors="coerce").astype("Int64")
    df["sic"] = df["sic"].astype("Int64")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / (f"headers_{year}.parquet" if not args.limit else f"test_headers_{year}.parquet")
    df.to_parquet(out, index=False)
    dt = time.time() - t0
    print(f"year {year}: {len(df):,} filings in {dt:.0f}s ({len(df) / max(dt, 1e-9):.0f}/s), "
          f"status {df.status.value_counts().to_dict()}, "
          f"no period {df.period_of_report.isna().sum()}, no sic {df.sic.isna().sum()} -> {out}")


if __name__ == "__main__":
    main()
