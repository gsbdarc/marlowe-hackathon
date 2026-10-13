"""Stages 2 and 3: extract the main document's text and split it into paragraphs with sections.

One pass per filing so the full text is never stored:
  main document -> text blocks (HTML, inline XBRL or plain text) -> drop numeric tables,
  page numbers, running headers and table-of-contents entries -> sections -> paragraphs.

Writes, per shard:
  data/interim/paragraphs/part-<shard>.parquet   one row per paragraph
  data/interim/extract/status-<shard>.parquet    one row per filing (status, format, counts)
scripts/03_check.py combines the status files into the Stage 2-3 checks.

Run as a Slurm array (slurm/02_extract.slurm), one task per shard. For a test on a few
fiscal years: python scripts/02_extract.py --test-years 1998 2008 2022 --limit 200
"""

import argparse
import hashlib
import os
import re
import time
from collections import Counter
from types import SimpleNamespace
from multiprocessing import Pool
from pathlib import Path

import lxml.html
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"

MIN_WORDS, MAX_WORDS, PREV_WORDS = 15, 400, 150
TOC_MIN_WORDS = 30          # an item heading followed by fewer words is a TOC entry or empty item
HEADING_MAX_WORDS = 12
READ_CHUNK = 1 << 20
MAX_MAIN_DOC = 200 << 20    # give up on a main document larger than 200 MB

# ---------------------------------------------------------------- reading


def read_main_doc(path):
    """Bytes between <TEXT> and </TEXT> of the first <DOCUMENT>, and its <TYPE>."""
    buf = bytearray()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(READ_CHUNK)
            if not chunk:
                break
            buf += chunk
            if b"</DOCUMENT>" in buf[-len(chunk) - 16:] or len(buf) > MAX_MAIN_DOC:
                break
    start = buf.find(b"<DOCUMENT>")
    if start < 0:
        raise ValueError("no <DOCUMENT>")
    end = buf.find(b"</DOCUMENT>", start)
    if end < 0:
        raise ValueError("main document not closed (or larger than 200 MB)")
    doc = bytes(buf[start:end])
    m = re.search(rb"<TYPE>([^\r\n<]+)", doc)
    t0, t1 = doc.find(b"<TEXT>"), doc.rfind(b"</TEXT>")
    if t0 < 0:
        raise ValueError("no <TEXT> in main document")
    return (m.group(1).strip().decode("latin-1") if m else None), doc[t0 + 6:t1 if t1 > t0 else len(doc)]


def decode(b):
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252", errors="replace")


HTML_SNIFF = re.compile(r"<(html|body|p|div|font|br)\b", re.I)

# ---------------------------------------------------------------- blocks

NUMERIC_CELL = re.compile(r"^[\s$€£()\-–—%,.*\d]*\d[\s$€£()\-–—%,.*\d]*$")
WS = re.compile(r"[\s ​]+")
BLOCK_TAGS = {"p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol",
              "center", "blockquote", "section", "article", "dt", "dd", "hr", "body"}
PAGE_NUM = re.compile(r"^(page\s*)?[-–—(]*\s*([a-z]{1,2}-?)?\d{1,3}\s*[-–—)]*$|^[ivxlc]{1,6}$", re.I)
TOC_LINE = re.compile(r"^(table of contents|index|\(?back to (top|contents)\)?|return to (top|table of contents))$", re.I)


def numeric_share(cells):
    cells = [c for c in cells if c]
    if not cells:
        return 0.0
    return sum(bool(NUMERIC_CELL.match(c)) for c in cells) / len(cells)


def html_blocks(text, stats):
    root = lxml.html.document_fromstring(text)
    for el in list(root.iter()):
        tag = el.tag if isinstance(el.tag, str) else ""
        style = (el.get("style") or "").replace(" ", "").lower() if tag else ""
        if tag in ("script", "style", "head", "title") or tag.endswith("header") and tag.startswith("ix") \
                or "display:none" in style:
            if el.getparent() is not None:
                stats["hidden_dropped"] += tag.startswith("ix")
                el.drop_tree()
    # Numeric tables out; text tables stay with one block per row. Innermost tables first.
    for table in reversed(list(root.iter("table"))):
        if table.getparent() is None:
            continue
        cells = [WS.sub(" ", td.text_content()).strip() for td in table.iter("td", "th")]
        if numeric_share(cells) > 0.5:
            stats["tables_dropped"] += 1
            table.drop_tree()
        else:
            stats["tables_kept"] += 1
    # Preformatted text inside HTML is handled like a plain-text filing.
    for pre in list(root.iter("pre")):
        paras = text_blocks(pre.text_content(), stats)
        pre.clear()
        pre.text = "\n\n" + "\n\n".join(paras) + "\n\n"
        pre.tag = "div"
    for el in root.iter():
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag in BLOCK_TAGS:
            el.text = "\n\n" + (el.text or "")
            el.tail = "\n\n" + (el.tail or "")
        elif tag == "br":
            el.tail = "\n" + (el.tail or "")
        elif tag in ("td", "th"):
            el.tail = " " + (el.tail or "")
    out = []
    for raw in re.split(r"\n[ \t ]*\n", root.text_content()):
        b = WS.sub(" ", raw).strip()
        if b:
            out.append(b)
    return out


SGML_TAG_LINE = re.compile(r"^\s*</?(PAGE|S|C|CAPTION|FN|F\d+|R\d+|SUP|U|B|I)>\s*$", re.I)
TEXT_TABLE = re.compile(r"<TABLE>(.*?)</TABLE>", re.I | re.S)


def text_blocks(text, stats):
    def table_sub(m):
        body = m.group(1)
        tokens = re.findall(r"\S+", re.sub(r"</?[A-Z]+>", " ", body))
        words = [t for t in tokens if re.search(r"[A-Za-z]{2,}", t)]
        nums = [t for t in tokens if NUMERIC_CELL.match(t)]
        if nums and len(nums) > len(words):
            stats["tables_dropped"] += 1
            return "\n\n"
        stats["tables_kept"] += 1
        return "\n\n" + body + "\n\n"

    text = TEXT_TABLE.sub(table_sub, text.replace("\r", ""))
    lines = [("" if SGML_TAG_LINE.match(l) else re.sub(r"</?[A-Z]{1,8}>", "", l)) for l in text.split("\n")]
    out, cur = [], []
    for line in lines + [""]:
        s = line.strip()
        if s:
            cur.append(s)
        elif cur:
            out.append(WS.sub(" ", " ".join(cur)).strip())
            cur = []
    return [b for b in out if b]


def clean_blocks(blocks, stats):
    """Drop page numbers, TOC lines and running headers (short blocks repeated 3+ times)."""
    short = Counter(b.lower() for b in blocks if len(b.split()) <= 10)
    out = []
    for b in blocks:
        if PAGE_NUM.match(b) or TOC_LINE.match(b):
            stats["page_or_toc_dropped"] += 1
        elif short.get(b.lower(), 0) >= 3 and not ITEM.match(b):
            stats["running_header_dropped"] += 1
        else:
            out.append(b)
    return out

# ---------------------------------------------------------------- sections

ITEM = re.compile(r"^\s*(?:part\s+[ivx]+\s*[,.:;\-–—]?\s*)?items?\s*(\d{1,2})(?:\s*\.\s*(\d{2}))?\s*([a-d])?\b\s*[.:;\-–—)]?\s*(.{0,160})", re.I)
TITLE_KEYS = [
    ("1C", re.compile(r"cyber\s*security", re.I)),
    ("1A", re.compile(r"risk\s+factors", re.I)),
    ("7", re.compile(r"management[’'`s]*\s*s?\s*discussion", re.I)),
]
RISK_HEADING = re.compile(r"^\s*risk\s+factors\s*[.:]?\s*$", re.I)
NOT_APPLICABLE = re.compile(r"not\s+(applicable|required)|smaller\s+reporting\s+compan", re.I)
REG_AB = re.compile(r"regulation\s+ab\b", re.I)
KSB_FORMS = {"10KSB", "10KSB40"}
TENK_FORMS = {"10-K", "10-K405", "10-KT", "10KT405"}


def item_section(m, next_block, form_type):
    """Map an item heading to 1A, 1C, 7, OTHER, or an 8-K item number like 1.05."""
    num, sub, letter, title = m.group(1), m.group(2), (m.group(3) or "").upper(), m.group(4) or ""
    if form_type == "8-K":
        return f"{int(num)}.{sub}" if sub else "OTHER"
    if sub:  # "Item 1.05" style outside an 8-K
        return "OTHER"
    probe = title if len(title.split()) >= 2 else f"{title} {next_block[:160]}"
    for label, rx in TITLE_KEYS:
        if rx.search(probe):
            return label
    code = f"{int(num)}{letter}"
    if form_type in TENK_FORMS and code in ("1A", "1C", "7"):
        return code
    if form_type in KSB_FORMS and code == "6":
        return "7"
    return "OTHER"


def assign_sections(blocks, form_type):
    """Section label for every block. Item headings followed by < TOC_MIN_WORDS words are skipped."""
    hits, item_1a_na = [], False
    for i, b in enumerate(blocks):
        if len(b.split()) > 60:
            continue
        m = ITEM.match(b)
        if m:
            nxt = blocks[i + 1] if i + 1 < len(blocks) else ""
            label = item_section(m, nxt, form_type)
            hits.append((i, label))
            if label == "1A" and NOT_APPLICABLE.search(f"{m.group(4)} {nxt}"[:300]):
                item_1a_na = True
        elif form_type != "8-K" and RISK_HEADING.match(b):
            # Small companies often put a bare "Risk Factors" heading inside Item 1.
            hits.append((i, "1A"))
    words = [len(b.split()) for b in blocks]
    starts = []
    for k, (i, label) in enumerate(hits):
        j = hits[k + 1][0] if k + 1 < len(hits) else len(blocks)
        between = sum(words[i + 1:j]) + max(0, words[i] - 12)
        if between >= TOC_MIN_WORDS:
            starts.append((i, label))
    sections = ["OTHER"] * len(blocks)
    for k, (i, label) in enumerate(starts):
        j = starts[k + 1][0] if k + 1 < len(starts) else len(blocks)
        for t in range(i, j):
            sections[t] = label
    return sections, {lab for _, lab in starts}, item_1a_na

# ---------------------------------------------------------------- paragraphs

SENT_SPLIT = re.compile(r"(?:(?<=[.!?])|(?<=[.!?][\"”’)]))\s+(?=[A-Z0-9\"“(])")


def chunk_long(text):
    words = text.split()
    if len(words) <= MAX_WORDS:
        return [text]
    chunks, cur, n = [], [], 0
    for s in SENT_SPLIT.split(text):
        k = len(s.split())
        if cur and n + k > MAX_WORDS:
            chunks.append(" ".join(cur))
            cur, n = [], 0
        if k > MAX_WORDS:  # one very long "sentence": cut at word boundaries
            ws = s.split()
            for x in range(0, len(ws), MAX_WORDS):
                chunks.append(" ".join(ws[x:x + MAX_WORDS]))
            continue
        cur.append(s)
        n += k
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def is_heading(b):
    n = len(b.split())
    return (n <= HEADING_MAX_WORDS and not b.rstrip().endswith((".", ",", ";"))) or bool(ITEM.match(b) and n <= 25)


def normalize(t):
    return WS.sub(" ", t.lower()).strip()


def paragraphs(row, blocks, sections):
    out, heading, prev = [], "", ""
    for b, sec in zip(blocks, sections):
        n = len(b.split())
        if n < MIN_WORDS:
            if is_heading(b):
                heading = b[:200]
            continue
        chunks = chunk_long(b)
        for c_i, text in enumerate(chunks):
            nw = len(text.split())
            if nw < MIN_WORDS:
                continue
            out.append({
                "para_id": f"{row.accession}_{len(out):05d}",
                "accession": row.accession, "cik": row.cik, "form_type": row.form_type,
                "fiscal_year": row.fiscal_year, "section": sec, "heading": heading,
                "prev_text": " ".join(prev.split()[-PREV_WORDS:]), "text": text, "n_words": nw,
                "chunk": c_i if len(chunks) > 1 else -1,
                "text_sha1": hashlib.sha1(normalize(text).encode()).hexdigest(),
            })
            prev = text
    return out

# ---------------------------------------------------------------- driver


def process(row):
    stats = Counter()
    st = {"accession": row.accession, "status": "ok", "error": None, "format": None, "main_type": None}
    try:
        doc_type, raw = read_main_doc(row.filepath)
        st["main_type"], st["main_bytes"] = doc_type, len(raw)
        text = decode(raw)
        if HTML_SNIFF.search(text[:20000]):
            st["format"] = "ixbrl" if re.search(r"<ix:", text[:200000], re.I) else "html"
            blocks = html_blocks(text, stats)
        else:
            st["format"] = "text"
            blocks = text_blocks(text, stats)
        blocks = clean_blocks(blocks, stats)
        sections, found, item_1a_na = assign_sections(blocks, row.form_type)
        paras = paragraphs(row, blocks, sections)
        st.update(n_blocks=len(blocks), n_paras=len(paras), n_words=sum(p["n_words"] for p in paras),
                  has_1a="1A" in found, has_1c="1C" in found, has_7="7" in found, item_1a_na=item_1a_na,
                  reg_ab=bool(REG_AB.search(text)),
                  items_8k=",".join(sorted(x for x in found if "." in x)), **stats)
        if not paras:
            st["status"] = "empty"
        return st, paras
    except Exception as e:
        st.update(status="failed", error=f"{type(e).__name__}: {e}"[:300])
        return st, []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shard", type=int, default=None, help="defaults to SLURM_ARRAY_TASK_ID")
    ap.add_argument("--n-shards", type=int, default=64)
    ap.add_argument("--workers", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", 4)))
    ap.add_argument("--test-years", type=int, nargs="*", help="test mode: sample annual reports from these fiscal years")
    ap.add_argument("--limit", type=int, default=200, help="filings per test year")
    args = ap.parse_args()

    f = pd.read_parquet(FINAL / "filings.parquet")
    if args.test_years:
        parts = [f[f.is_annual & (f.fiscal_year == y)].sample(args.limit, random_state=y) for y in args.test_years]
        todo, tag = pd.concat(parts), "test"
    else:
        shard = args.shard if args.shard is not None else int(os.environ["SLURM_ARRAY_TASK_ID"])
        f = f.sort_values("accession").reset_index(drop=True)
        todo, tag = f[f.index % args.n_shards == shard], f"{shard:03d}"
    # Big files first so one large filing does not finish the shard late.
    todo = todo.sort_values("file_bytes", ascending=False)

    t0 = time.time()
    with Pool(args.workers, maxtasksperchild=200) as pool:
        rows = [SimpleNamespace(**r) for r in todo.to_dict("records")]  # picklable, unlike itertuples rows
        results = pool.map(process, rows, chunksize=4)
    status = pd.DataFrame([s for s, _ in results])
    paras = pd.DataFrame([p for _, ps in results for p in ps])

    for sub in ("paragraphs", "extract"):
        (INTERIM / sub).mkdir(parents=True, exist_ok=True)
    if len(paras):
        paras["fiscal_year"] = pd.to_numeric(paras.fiscal_year).astype("Int64")
    paras.to_parquet(INTERIM / "paragraphs" / f"part-{tag}.parquet", index=False, compression="zstd")
    status.to_parquet(INTERIM / "extract" / f"status-{tag}.parquet", index=False)
    dt = time.time() - t0
    print(f"shard {tag}: {len(todo):,} filings, {len(paras):,} paragraphs in {dt:.0f}s; "
          f"status {status.status.value_counts().to_dict()}; format {status.format.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
