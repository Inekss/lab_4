from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


class CorpusReader:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def iter_documents(self) -> Iterator[str]:
        for file in self.path.glob("*.txt"):
            yield file.read_text(encoding="utf-8")

    def iter_docs(self) -> Iterator[tuple[int, Path, str]]:
        # sorted paths keep doc_id stable; ids only increase, so postings stay in order
        for doc_id, file in enumerate(sorted(self.path.glob("*.txt"))):
            yield doc_id, file, file.read_text(encoding="utf-8")
