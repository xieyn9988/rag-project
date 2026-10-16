"""上下文注入策略（对齐 JD『上下文注入』）：去重 → 排序摆放 → 截断。"""
from __future__ import annotations
from difflib import SequenceMatcher

def dedupe_chunks(chunks: list[tuple[str, str, float]], threshold: float = 0.85):
    """文本相似去重：与已保留片段重叠率 > threshold 的丢弃。O(n²) 但 n≤10 无所谓。"""
    kept: list[tuple[str, str, float]] = []
    for cid, text, score in chunks:
        if all(SequenceMatcher(None, text, t).ratio() < threshold for _, t, _ in kept):
            kept.append((cid, text, score))
    return kept

def lost_in_middle_ordering(chunks: list[tuple[str, str, float]]):
    """应对 lost-in-the-middle：最高分放首位，次高分放末位，中间放其余。
    供消融：False = 纯降序摆放。"""
    if len(chunks) < 3:
        return chunks
    return [chunks[0], *chunks[2:], chunks[1]]

def truncate(chunks: list[tuple[str, str, float]], max_chars: int = 1600):
    out, used = [], 0
    for cid, text, score in chunks:
        if used + len(text) > max_chars:
            break
        out.append((cid, text, score)); used += len(text)
    return out

def build_context(chunks, dedupe=True, reorder=True, max_chars=1600):
    if dedupe: chunks = dedupe_chunks(chunks)
    if reorder: chunks = lost_in_middle_ordering(chunks)
    return truncate(chunks, max_chars)
