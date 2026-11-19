"""Library: parse markdown docs, build a SQLite FTS5 index, search it."""
import re
import sqlite3
from dataclasses import dataclass

from . import config

STOPWORDS = set("""a an and are as at be but by can could do does for from how i if in
into is it its me my of on or should so that the their them then there these they this
to was what when where which who why will with would you your about any get got have""".split())


# Small hand-made synonym list so plain-language questions find the right
# section. Replace with embedding search once the library grows.
SYNONYMS = {
    "purify": ["treat", "boil", "disinfect", "filter"],
    "purifying": ["treat", "boil", "disinfect", "filter"],
    "clean": ["treat", "boil", "disinfect"],
    "drinkable": ["treat", "boil"],
    "drink": ["water"],
    "cold": ["hypothermia", "warm"],
    "freezing": ["hypothermia", "warm"],
    "rash": ["poison", "oak", "wash"],
    "itchy": ["poison", "oak", "wash"],
    "snake": ["rattlesnake"],
    "snakes": ["rattlesnake"],
}


@dataclass
class Passage:
    doc_id: str
    title: str
    section: str
    text: str
    source: str
    date: str
    vetted: bool
    region: str


def parse_doc(path):
    raw = path.read_text(encoding="utf-8")
    meta, body = {}, raw
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    title = meta.get("title", path.stem)
    sections, current, buf = [], title, []
    for line in body.strip().splitlines():
        if line.startswith("## "):
            if "".join(buf).strip():
                sections.append((current, "\n".join(buf).strip()))
            current, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((current, "\n".join(buf).strip()))
    return meta, title, sections


def build_index():
    config.INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if config.INDEX_PATH.exists():
        config.INDEX_PATH.unlink()
    con = sqlite3.connect(config.INDEX_PATH)
    con.execute("""CREATE VIRTUAL TABLE chunks USING fts5(
        title, section, text,
        doc_id UNINDEXED, region UNINDEXED, source UNINDEXED,
        date UNINDEXED, vetted UNINDEXED, ord UNINDEXED,
        tokenize='porter unicode61')""")
    n = 0
    for path in sorted(config.LIBRARY_DIR.rglob("*.md")):
        meta, title, sections = parse_doc(path)
        for i, (section, text) in enumerate(sections):
            con.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?)", (
                title, section, text, path.stem, meta.get("region", "core"),
                meta.get("source", "unknown"), meta.get("date", "?"),
                meta.get("vetted", "false"), i))
            n += 1
    con.commit()
    con.close()
    return n


class Library:
    def __init__(self, region=config.REGION):
        if not config.INDEX_PATH.exists():
            build_index()
        self.con = sqlite3.connect(config.INDEX_PATH, check_same_thread=False)
        self.region = region

    @staticmethod
    def _row(r):
        title, section, text, doc_id, region, source, date, vetted = r[:8]
        return Passage(doc_id, title, section, text, source, date,
                       str(vetted).lower() == "true", region)

    def search(self, query, k=config.MAX_PASSAGES):
        terms = [t for t in re.findall(r"[a-z0-9]+", query.lower())
                 if t not in STOPWORDS and len(t) > 1]
        if not terms:
            return []
        expanded = {t: [t] + SYNONYMS.get(t, []) for t in terms}
        fts = " OR ".join(f'"{w}"' for ws in expanded.values() for w in ws)
        rows = self.con.execute("""
            SELECT title, section, text, doc_id, region, source, date, vetted,
                   bm25(chunks, 5.0, 3.0, 1.0) AS score
            FROM chunks WHERE chunks MATCH ? AND region IN ('core', ?)
            ORDER BY score LIMIT 12""", (fts, self.region)).fetchall()
        # Require that a chunk covers enough of the question, so one stray
        # common word doesn't produce a confident-looking answer.
        need = 1 if len(terms) <= 2 else 2
        scored = []
        for r in rows:
            hay = f"{r[0]} {r[1]} {r[2]}".lower()
            hits = sum(1 for ws in expanded.values() if any(w[:5] in hay for w in ws))
            if hits >= need:
                scored.append((-hits, r[8], r))
        scored.sort(key=lambda x: (x[0], x[1]))
        return [self._row(r) for _, _, r in scored[:k]]

    def docs(self):
        return self.con.execute("""SELECT DISTINCT doc_id, title, region FROM chunks
            WHERE region IN ('core', ?) ORDER BY region, title""", (self.region,)).fetchall()

    def doc_sections(self, doc_id):
        rows = self.con.execute("""SELECT title, section, text, doc_id, region, source, date, vetted
            FROM chunks WHERE doc_id = ? ORDER BY CAST(ord AS INTEGER)""", (doc_id,)).fetchall()
        return [self._row(r) for r in rows]


def load_cards():
    cards = {}
    for path in sorted(config.CARDS_DIR.glob("*.md")):
        meta, title, sections = parse_doc(path)
        body = "\n".join(t for _, t in sections)
        steps = [re.sub(r"^\d+\.\s*", "", l.strip()) for l in body.splitlines()
                 if re.match(r"^\d+\.", l.strip())]
        notes = [l.strip()[2:] for l in body.splitlines() if l.strip().startswith("- ")]
        cid = meta.get("id", path.stem)
        cards[cid] = {"id": cid, "title": title, "steps": steps, "notes": notes,
                      "source": meta.get("source", "unknown"),
                      "vetted": meta.get("vetted", "false").lower() == "true",
                      "order": int(meta.get("order", 99))}
    return dict(sorted(cards.items(), key=lambda kv: kv[1]["order"]))
