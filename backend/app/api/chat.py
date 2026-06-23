import json
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag.engine import process_query, stream_query

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


# ─────────────────────────────────────────────
#  Standard (non-streaming) endpoint
# ─────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Câu hỏi không được rỗng")

    try:
        start_time = time.time()
        answer = await process_query(question)
        elapsed = time.time() - start_time

        print(f"💡 [Tốc độ] Hoàn thành trong: {elapsed:.2f} giây")

        return {"answer": answer.strip()}

    except Exception as e:
        print(f"Lỗi khi xử lý câu hỏi: {e}")
        raise HTTPException(
            status_code=500,
            detail="Xin lỗi bạn, máy chủ đang bận. Thử lại sau nhé!",
        )


# ─────────────────────────────────────────────
#  Streaming endpoint — Server-Sent Events
# ─────────────────────────────────────────────

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streams the LLM response token-by-token via Server-Sent Events (SSE).

    SSE event format:
      data: {"token": "<text>"}\\n\\n   — incremental token
      data: [DONE]\\n\\n                — stream finished

    Frontend usage (fetch):
      const res = await fetch('/api/chat/stream', { method: 'POST', ... })
      const reader = res.body.getReader()
      // read chunks and display progressively

    Frontend usage (EventSource workaround via POST):
      Use the fetchEventSource library from @microsoft/fetch-event-source.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Câu hỏi không được rỗng")

    async def generate():
        try:
            async for token in stream_query(question):
                payload = json.dumps({"token": token}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except Exception as e:
            error_payload = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
