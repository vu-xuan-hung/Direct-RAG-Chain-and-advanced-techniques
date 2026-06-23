"""
RAG Engine — Direct Chain (no LangGraph Agent overhead).

Optimization history:
  v2 (current): Agent → Direct Chain + TTL retrieval cache
    - Eliminates 1 LLM call (agent tool-decision step)
    - Rule-based greeting detection (0ms vs ~30s with LLM)
    - TTL cache: repeated queries served instantly from memory
"""
import time
import hashlib
import threading
from typing import Optional, AsyncGenerator

from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage

from core.config import settings
from core.device import DEVICE
from transformation.query_decomposition import QueryDecomposer
from transformation.hyde import HyDEGenerator
from transformation.transformation_router import TransformationRouter
from post_retrieval.post_retrieval_pipeline import PostRetrievalPipeline
from retrieval.hybrid_search import HybridSearch
from retrieval.bm25_retriever import get_shared_bm25
from retrieval.query_router import QueryRouter
from concurrent.futures import ThreadPoolExecutor


# ─────────────────────────────────────────────
#  Shared models (initialized once at startup)
# ─────────────────────────────────────────────

def _build_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
    )


embed_model = HuggingFaceEmbeddings(
    model_name=settings.EMBEDDING_MODEL,
    model_kwargs={'device': DEVICE}
)

# Transformation layer
queryde       = QueryDecomposer(llm=_build_llm())
hyde_gen      = HyDEGenerator(llm=_build_llm(), embed=embed_model)
route_transform = TransformationRouter(llm=_build_llm())

# Post-retrieval
post_retrieval_pipeline = PostRetrievalPipeline(
    embeddings_model=embed_model,
    cross_encoder_model_name=settings.CROSS_ENCODER_MODEL,
    device=settings.CROSS_ENCODER_DEVICE
)

# Retrieval
hybrid_search    = HybridSearch()
bm25_retriever   = get_shared_bm25()   # reuses the singleton loaded by hybrid_search
router_retriever = QueryRouter()

# Singleton LLM for answer generation
_answer_llm: Optional[ChatOllama] = None
_llm_lock = threading.Lock()

def get_answer_llm() -> ChatOllama:
    global _answer_llm
    if _answer_llm is None:
        with _llm_lock:
            if _answer_llm is None:
                _answer_llm = _build_llm()
    return _answer_llm


# ─────────────────────────────────────────────
#  TTL Cache — retrieval results
# ─────────────────────────────────────────────

class TTLCache:
    """
    Thread-safe in-memory cache with per-entry TTL and a max-size cap.
    Stores final retrieval context strings keyed by MD5(query).
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 256):
        self._store: dict[str, tuple[str, float]] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._lock = threading.Lock()

    def _make_key(self, query: str) -> str:
        return hashlib.md5(query.strip().lower().encode("utf-8")).hexdigest()

    def get(self, query: str) -> Optional[str]:
        key = self._make_key(query)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, ts = entry
            if time.time() - ts < self.ttl:
                return value
            # Expired
            del self._store[key]
        return None

    def set(self, query: str, value: str) -> None:
        key = self._make_key(query)
        with self._lock:
            # Evict oldest entry when at capacity
            if key not in self._store and len(self._store) >= self.max_size:
                oldest_key = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest_key]
            self._store[key] = (value, time.time())

    def stats(self) -> dict:
        with self._lock:
            return {"size": len(self._store), "max_size": self.max_size, "ttl": self.ttl}


retrieval_cache = TTLCache(
    ttl_seconds=settings.CACHE_TTL_SECONDS,
    max_size=settings.CACHE_MAX_SIZE,
)


# ─────────────────────────────────────────────
#  Greeting detection (rule-based, 0ms)
# ─────────────────────────────────────────────

_GREETING_KEYWORDS = {
    "xin chào", "chào", "hello", "hi", "hey",
    "cảm ơn", "camon", "tks", "thanks", "thank you",
    "tạm biệt", "bye", "goodbye",
    "ok", "okay", "oke", "được rồi",
}

_GREETING_RESPONSE = (
    "Xin chào! Mình là trợ lý Nhân sự của FPT. "
    "Bạn cần hỏi gì về chính sách, quy định hoặc quyền lợi nhân viên không? 😊"
)


def _is_greeting(text: str) -> bool:
    words = text.strip().lower().split()
    if len(words) > 6:
        return False
    return any(kw in " ".join(words) for kw in _GREETING_KEYWORDS)


# ─────────────────────────────────────────────
#  Retrieval pipeline (with cache)
# ─────────────────────────────────────────────

def _retrieve_single_query(sq: str) -> list:
    route = router_retriever.route(sq)
    if route == "keyword":
        print(f"[RETRIEVAL] Dùng BM25 tìm: '{sq[:80]}'")
        return bm25_retriever.invoke(sq)
    else:
        print(f"[RETRIEVAL] Dùng Hybrid tìm: '{sq[:80]}'")
        return hybrid_search.invoke(sq)


def retrieve_context(query: str) -> str:
    """
    Full 3-layer retrieval pipeline:
      1. Query transformation (routing → HyDE / decompose / direct)
      2. Parallel retrieval (Hybrid or BM25)
      3. Post-retrieval reranking (Cross-Encoder + MMR)

    Results are cached by query for `CACHE_TTL_SECONDS`.
    """
    # ── Cache check ──────────────────────────────────
    cached = retrieval_cache.get(query)
    if cached is not None:
        print(f"[CACHE HIT] Serving from cache — stats: {retrieval_cache.stats()}")
        return cached

    # ── Layer 1: Transformation ──────────────────────
    route_trans = route_transform.route_query(query)
    print(f"[ROUTER DETECTED PATH] Mode: '{route_trans}'")

    search_queries: list[str] = []
    if route_trans == "complex":
        sub_qs = queryde.decompose(query)
        search_queries.extend(sub_qs)
        print(f"[DECOMPOSER] Các câu hỏi con: {sub_qs}")
    elif route_trans == "vague":
        hyx = hyde_gen.generate_hypothetical_answer(query)
        print(f"Hypothetical answer generated for query '{query}':\n{hyx}\n")
        search_queries.append(hyx)
    else:
        search_queries.append(query)

    # ── Layer 2: Parallel retrieval ──────────────────
    with ThreadPoolExecutor(max_workers=max(1, len(search_queries))) as executor:
        results = list(executor.map(_retrieve_single_query, search_queries))

    all_docs = [doc for docs in results for doc in docs]
    unique_docs = list({doc.page_content: doc for doc in all_docs}.values())

    # ── Layer 3: Post-retrieval reranking ────────────
    final_docs = post_retrieval_pipeline.run_pipeline(
        query=query,
        candidate_docs=unique_docs,
        order=settings.SEARCH_ORDER,
        ce_top_k=6,
        mmr_top_k=3,
        mmr_lambda=0.5,
    )

    final_context = "\n\n======\n\n".join(doc.page_content for doc in final_docs)

    # ── Cache result ──────────────────────────────────
    retrieval_cache.set(query, final_context)

    return final_context


# ─────────────────────────────────────────────
#  System prompt
# ─────────────────────────────────────────────

_SYSTEM_PROMPT = """Bạn là trợ lý Nhân sự (HR) mẫn cán của tập đoàn FPT.
Trả lời câu hỏi của nhân viên một cách thân thiện, ngắn gọn và mạch lạc. Chủ động xưng "mình" và gọi "bạn".

Tuyệt đối không tự bịa thông tin. Dựa 100% vào dữ liệu tìm được trong ngữ cảnh bên dưới.
Nếu ngữ cảnh không chứa thông tin liên quan, hãy thành thật trả lời là mình không tìm thấy thông tin về vấn đề này.
"""


def _build_prompt(question: str, context: str) -> str:
    # Trim context to MAX_CONTEXT_CHARS to reduce LLM token load
    if len(context) > settings.MAX_CONTEXT_CHARS:
        context = context[:settings.MAX_CONTEXT_CHARS] + "\n[... nội dung được rút gọn ...]"

    return (
        f"{_SYSTEM_PROMPT}\n\n"
        f"--- Ngữ cảnh chính sách FPT ---\n{context}\n\n"
        f"--- Câu hỏi ---\n{question}"
    )


# ─────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────

async def process_query(question: str) -> str:
    """
    Direct RAG chain (no agent overhead):
      1. Greeting check (0ms)
      2. Retrieval pipeline (cached)
      3. Single LLM call for answer generation
    """
    # Fast path: greeting
    if _is_greeting(question):
        print(f"[GREETING DETECTED] Skipping retrieval for: '{question}'")
        return _GREETING_RESPONSE

    print(f"\n[DIRECT RAG] Câu hỏi: '{question}'")

    # Retrieval (cache-aware)
    t0 = time.time()
    context = retrieve_context(question)
    print(f"[TIMING] Retrieval: {time.time() - t0:.2f}s")

    # Single LLM call
    t1 = time.time()
    llm = get_answer_llm()
    response = await llm.ainvoke([HumanMessage(content=_build_prompt(question, context))])
    print(f"[TIMING] LLM answer: {time.time() - t1:.2f}s")

    return response.content


async def stream_query(question: str) -> AsyncGenerator[str, None]:
    """
    Streaming variant — yields tokens as they are generated.
    Retrieval is the same (cached) but LLM response is streamed
    token-by-token so the user sees output immediately.
    """
    # Fast path: greeting
    if _is_greeting(question):
        print(f"[GREETING DETECTED] Streaming greeting for: '{question}'")
        yield _GREETING_RESPONSE
        return

    print(f"\n[STREAM RAG] Câu hỏi: '{question}'")

    # Retrieval (cache-aware — same as process_query)
    t0 = time.time()
    context = retrieve_context(question)
    print(f"[TIMING] Retrieval: {time.time() - t0:.2f}s")

    # Stream LLM tokens
    t1 = time.time()
    llm = get_answer_llm()
    first_token = True
    async for chunk in llm.astream([HumanMessage(content=_build_prompt(question, context))]):
        if chunk.content:
            if first_token:
                print(f"[TIMING] First token: {time.time() - t1:.2f}s")
                first_token = False
            yield chunk.content
    print(f"[TIMING] LLM stream total: {time.time() - t1:.2f}s")
