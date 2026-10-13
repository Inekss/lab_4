from __future__ import annotations

import gc
import tracemalloc
from array import array
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter

from findex.deco import timed
from findex.documents import CorpusReader
from findex.models import DocMeta, Index, Posting, PostingPlain
from findex.store import pickle_size_and_load, timed_save_load
from findex.tokenizer import Tokenizer

CORPUS = Path(__file__).resolve().parents[1] / "resources"
OUT_PKL = Path(__file__).resolve().parents[2] / "index.pkl"
OUT_JSON = Path(__file__).resolve().parents[2] / "index.json"
WITH_POSITIONS = True  # phrase queries need token offsets


@timed
def build(reader: CorpusReader, tok: Tokenizer, with_positions: bool = False) -> Index:
    postings: dict[str, list[Posting]] = defaultdict(list)
    doc_lengths: dict[int, int] = {}
    doc_meta: dict[int, DocMeta] = {}
    for doc_id, path, text in reader.iter_docs():
        counts: Counter[str] = Counter()
        pos: dict[str, list[int]] | None = defaultdict(list) if with_positions else None
        n = 0
        for i, term in enumerate(tok.tokenize(text)):
            counts[term] += 1
            n += 1
            if pos is not None:
                pos[term].append(i)
        doc_lengths[doc_id] = n
        doc_meta[doc_id] = DocMeta(str(path), path.stem)
        for term, tf in counts.items():
            positions = tuple(pos[term]) if pos is not None else ()
            postings[term].append(Posting(doc_id, tf, positions))
    # merge lists; doc_id order is the contract
    for plist in postings.values():
        plist.sort(key=lambda p: p.doc_id)
    return Index(dict(postings), doc_lengths, doc_meta)


def build_variant(reader: CorpusReader, tok: Tokenizer, kind: str):
    if kind == "array":
        # 'I' = 4-byte unsigned ints, no Posting objects
        postings = defaultdict(lambda: (array("I"), array("I")))
    else:
        postings = defaultdict(list)
    cls = PostingPlain if kind == "plain" else Posting
    doc_lengths: dict[int, int] = {}
    doc_meta: dict[int, DocMeta] = {}
    for doc_id, path, text in reader.iter_docs():
        counts = Counter(tok.tokenize(text))
        doc_lengths[doc_id] = sum(counts.values())
        doc_meta[doc_id] = DocMeta(str(path), path.stem)
        for term, tf in counts.items():
            if kind == "array":
                postings[term][0].append(doc_id)
                postings[term][1].append(tf)
            else:
                postings[term].append(cls(doc_id, tf))
    return {"postings": dict(postings), "doc_lengths": doc_lengths, "doc_meta": doc_meta}


def _peak_kib(fn):
    gc.collect()
    tracemalloc.start()
    obj = fn()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return obj, peak / 1024


def positions_cost() -> None:
    reader, tok = CorpusReader(CORPUS), Tokenizer()
    for flag in (False, True):
        index, peak = _peak_kib(lambda flag=flag: build(reader, tok, flag))
        size, load_s = pickle_size_and_load(index)
        print(f"positions={flag} peak={peak:.1f}KiB pickle={size} load={load_s:.4f}s")
        del index
        gc.collect()


def memory_study() -> None:
    reader, tok = CorpusReader(CORPUS), Tokenizer()
    for kind in ("plain", "slots", "array"):
        obj, peak = _peak_kib(lambda kind=kind: build_variant(reader, tok, kind))
        size, load_s = pickle_size_and_load(obj)
        print(f"{kind} peak={peak:.1f}KiB file={size} load={load_s:.4f}s")
        del obj
        gc.collect()


def main() -> Index:
    reader, tok = CorpusReader(CORPUS), Tokenizer()
    tracemalloc.start()
    t0 = perf_counter()
    index = build(reader, tok, WITH_POSITIONS)
    elapsed = perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(
        f"{index!r} tokens={sum(index.doc_lengths.values())} "
        f"time={elapsed:.4f}s peak={peak / 1024:.1f}KiB"
    )
    timed_save_load(index, OUT_PKL, OUT_JSON)
    return index


if __name__ == "__main__":
    main()
