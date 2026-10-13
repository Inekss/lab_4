# findex

Ranked search over `src/resources/*.txt` — **one `.txt` file = one document** (three Harry Potter books).

From `src/`: `python main.py` builds the index, prints the checks below, then runs the demo query twice inside `with open_index`.

## Index

`WITH_POSITIONS = True`. One build:

`Index(terms=12_290, docs=3)` — 267845 tokens, 1.0037 s, peak 16530.8 KiB.

## Ranking checks (BM25, k1=1.5, b=0.75)

Same tf and the same document length. Only `df` changes. `quirrell` is in one book, `norbert` in two.

| term | df | weight at tf=1 |
|------|----|----------------|
| quirrell | 1 | 1.1673 |
| norbert | 2 | 0.4308 |

The rare term weighs more.

Marginal gain for `quirrell` on book 1’s length. The 20th occurrence adds 0.0085; the first added 1.1673.

| tf | weight | step from tf−1 |
|----|--------|----------------|
| 1 | 1.1673 | 1.1673 |
| 2 | 1.6383 | 0.4710 |
| 20 | 2.5725 | 0.0085 |
| 21 | 2.5803 | 0.0078 |

Same term, tf 1. The short book wins at `b=0.75`. At `b=0` the length term drops out and the weights match.

| document | tokens | b=0.75 | b=0 |
|----------|--------|--------|-----|
| harry_potter_1 | 77600 | 1.1673 | 1.0986 |
| harry_potter_3 | 104945 | 1.0182 | 1.0986 |

## precision@5

Ten hand-labeled queries. A hit counts when the labeled book is in the top 5. Precision divides by 5. Each query has one labeled book and that book is the only hit, so every cell is 1/5 = 0.20. Three documents cannot push a retrieved hit past rank 5, so TF-IDF and BM25 tie.

| query | TF-IDF | BM25 |
|-------|--------|------|
| quirrell | 0.20 | 0.20 |
| flamel | 0.20 | 0.20 |
| firenze | 0.20 | 0.20 |
| basilisk | 0.20 | 0.20 |
| lockhart | 0.20 | 0.20 |
| dobby | 0.20 | 0.20 |
| "chamber of secrets" | 0.20 | 0.20 |
| buckbeak | 0.20 | 0.20 |
| lupin | 0.20 | 0.20 |
| pettigrew | 0.20 | 0.20 |
| **mean** | **0.20** | **0.20** |

## @timed and cache

`logging` at DEBUG. `build`, `load_pickle`, `_unpickle`, and `search` log milliseconds. The demo query runs twice on the loaded index. The second call logs `cache hit` and `CacheInfo(hits=1, misses=1)`.

```text
build took 1003.4 ms
load_pickle took 51.6 ms
_unpickle took 50.3 ms
cache miss (quirrell OR buckbeak) AND harry NOT lockhart "privet drive"
search took 3.4 ms
cache hit (quirrell OR buckbeak) AND harry NOT lockhart "privet drive"
search took 2.0 ms
cache CacheInfo(hits=1, misses=1, maxsize=256, currsize=1)
```

## Demo query

`(quirrell OR buckbeak) AND harry NOT lockhart "privet drive"` with BM25. Book 2 drops out (`lockhart`). Snippets are ±80 characters; matched terms are in `[brackets]`.

| rank | score | title | snippet |
|------|-------|-------|---------|
| 1 | 2.7059 | harry_potter_1 | …"Professor [Quirrell]!" said Hagrid. "[Harry], Professor [Quirrell] will be one of your teachers at Hogwa… |
| 2 | 2.6857 | harry_potter_3 | …"Good man, [Harry]!" roared Hagrid. "Right then -- let's see how yeh get on with [Buckbeak]."… |
