"""
Manual Agent: retrieves the most relevant passages from the vehicle owner's manual.

The original version loaded PyTorch + a sentence-transformers model to query the
FAISS index. That needs far more RAM/CPU than Render's free instance has (512 MB),
so the server froze or crashed on the first manual lookup and the frontend showed
"TELEMETRY LINK OFFLINE".

This version keeps the same manual chunks (exported from the original FAISS
docstore in vectorstore/index.pkl into data/manual_chunks.json) and ranks them
with BM25 keyword scoring in pure Python: no model download, ~20 MB of memory,
and a lookup takes a few milliseconds.
"""

import json
import math
import os
import re
import time
from collections import Counter

CHUNKS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "manual_chunks.json")

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "am", "i", "my", "me", "we",
    "you", "your", "it", "its", "this", "that", "these", "those", "of", "in", "on", "at", "to",
    "for", "from", "with", "and", "or", "but", "if", "so", "do", "does", "did", "what", "why",
    "how", "when", "where", "which", "who", "can", "could", "should", "would", "will", "has",
    "have", "had", "not", "no", "yes", "there", "here", "car", "vehicle", "please", "help",
    "about", "just", "keeps", "keep", "getting", "get", "got", "very", "too", "also", "some",
}

# Everyday words mapped to the vocabulary the manual actually uses.
SYNONYMS = {
    "tyre": ["tire"], "tyres": ["tire"], "puncture": ["flat", "tire"], "punctured": ["flat", "tire"],
    "overheating": ["overheat", "coolant", "temperature"], "overheat": ["coolant", "temperature"],
    "overheated": ["overheat", "coolant", "temperature"], "hot": ["overheat", "temperature"],
    "heating": ["overheat", "temperature"], "smoke": ["steam", "overheat"],
    "battery": ["charg", "battery"], "flashing": ["warn", "light"], "dashboard": ["warn", "light", "indicator"],
    "brakes": ["brake"], "braking": ["brake"], "pads": ["brake", "pad"],
    "rain": ["wiper", "wet", "rain"], "raining": ["wiper", "wet", "rain"], "fog": ["fog", "light"],
    "oil": ["oil", "pressure"], "leak": ["leak", "fluid"], "leaking": ["leak", "fluid"],
    "start": ["start", "engine"], "starting": ["start", "engine"], "dead": ["battery", "discharg"],
    "ac": ["air", "condition"], "steering": ["steer"], "pressure": ["pressure"],
    "noise": ["noise", "sound", "abnormal"], "vibration": ["vibration", "abnormal"],
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _stem(word):
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _tokens(text):
    return [_stem(t) for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


def _query_tokens(query):
    words = [w for w in TOKEN_RE.findall(query.lower()) if w not in STOPWORDS and len(w) > 1]
    expanded = []
    for w in words:
        expanded.append(_stem(w))
        for syn in SYNONYMS.get(w, []):
            expanded.append(_stem(syn))
    return expanded


class _BM25Index:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.doc_tf = []
        self.doc_len = []
        # Table-of-contents / index pages match many keywords but carry no guidance.
        self.weight = [0.3 if chunk["t"].count("....") >= 3 else 1.0 for chunk in chunks]
        df = Counter()
        for chunk in chunks:
            tf = Counter(_tokens(chunk["t"]))
            self.doc_tf.append(tf)
            self.doc_len.append(sum(tf.values()))
            df.update(tf.keys())
        n = len(chunks)
        self.avgdl = (sum(self.doc_len) / n) if n else 1.0
        self.idf = {term: math.log(1 + (n - f + 0.5) / (f + 0.5)) for term, f in df.items()}

    def search(self, query, k=5):
        q_terms = Counter(_query_tokens(query))
        if not q_terms:
            return []
        scores = []
        for i, tf in enumerate(self.doc_tf):
            score = 0.0
            dl = self.doc_len[i] or 1
            for term, q_weight in q_terms.items():
                f = tf.get(term)
                if not f:
                    continue
                idf = self.idf.get(term, 0.0)
                score += q_weight * idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            if score > 0:
                scores.append((score * self.weight[i], i))
        scores.sort(reverse=True)
        return [self.chunks[i] for _, i in scores[:k]]


_index = None


def get_index():
    global _index
    if _index is None:
        start = time.time()
        try:
            with open(CHUNKS_PATH, encoding="utf-8") as fh:
                chunks = json.load(fh)
            _index = _BM25Index(chunks)
            print(f"Manual Agent ready: {len(chunks)} chunks indexed in {time.time() - start:.2f}s")
        except Exception as e:
            print("Error loading manual chunks:", e)
            _index = "FAILED"
    return _index


def _clean(text):
    # Drop the running header line that the PDF repeats on every page.
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("INNOVA_OM_")]
    return "\n".join(lines)


def retrieve_manual_info(query, k=5):
    print("\n========== Manual Agent ==========")
    print("Query:", query)
    start = time.time()

    index = get_index()
    if index == "FAILED" or index is None:
        return "Unable to retrieve information from the vehicle manual."

    try:
        docs = index.search(query, k=k)
        print(f"Retrieved {len(docs)} relevant chunks in {time.time() - start:.3f}s")
        if not docs:
            return "No matching section was found in the vehicle manual for this issue."
        return "\n\n".join(f"[Manual p.{d['p']}]\n{_clean(d['t'])}" for d in docs)
    except Exception as e:
        print("Manual Agent Error:", e)
        return "Unable to retrieve information from the vehicle manual."


if __name__ == "__main__":
    for q in ["My engine is overheating", "Brake warning light is on", "Tire pressure warning light is on"]:
        print(retrieve_manual_info(q, k=2)[:600])
