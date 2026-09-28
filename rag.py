"""
RAG query engine with conversation memory + voice output.

Usage (CLI):
    python rag.py "What is a left join?"
    python rag.py --speak "What is a left join?"
    python rag.py --voice "Microsoft Zira Desktop" --speak "..."
"""
import argparse
import sys
from dataclasses import dataclass

from config import GROQ_MODEL, TOP_K, SIMILARITY_THRESHOLD
from llm.client import get_groq_client
from vectorstore import VectorStore


@dataclass
class Source:
    source: str
    page: int
    distance: float
    snippet: str


@dataclass
class Answer:
    text: str
    sources: list[Source]
    refused: bool = False
    rewritten_question: str | None = None  # for debugging


SYSTEM_PROMPT = """You are a precise document assistant.

RULES:
1. Answer ONLY using the CONTEXT provided below.
2. If the answer is not contained in the CONTEXT, respond exactly:
   "I don't know based on the provided documents."
3. Do NOT use outside knowledge. Do NOT guess.
4. Always cite sources inline using PLAIN ASCII SQUARE BRACKETS ONLY:
   [filename.md, p.1]
   NEVER use 【】, ［］, （）, or any other bracket style.
5. Keep answers concise and factual. Quote short phrases when useful.
6. Use the conversation history to understand follow-up questions
   (e.g. pronouns, "what about X?", "and in Spark?"). But ONLY answer from CONTEXT.
"""

REWRITE_PROMPT = """You rewrite a user's follow-up question into a standalone question.

Rules:
- Include the topic from the previous turn.
- Preserve the user's intent.
- Output ONLY the rewritten question. No explanation, no quotes.

Example:
Previous Q: What is a left join?
Follow-up:  What about in Spark?
Output:     What is a left join in Spark?
"""


class RAGEngine:
    def __init__(self, store: VectorStore | None = None):
        self.store = store or VectorStore()
        self.client = get_groq_client()

    # ---------- Query rewriting ----------

    def _rewrite_query(self, question: str, history: list[dict]) -> str:
        """Turn a follow-up into a standalone question using last few turns."""
        if not history:
            return question

        # Only pass the last few user turns to keep the prompt small
        recent = [t for t in history if t["role"] == "user"][-3:]
        if not recent:
            return question

        # If the current question already looks standalone, skip rewriting
        if len(question.split()) >= 6 and not _looks_like_followup(question):
            return question

        history_text = "\n".join(f"- {t['text']}" for t in recent[:-1])
        last_q = recent[-1]["text"] if recent else ""

        rewrite_input = (
            f"Previous questions:\n{history_text}\n"
            f"Previous Q: {last_q}\n"
            f"Follow-up:  {question}\n"
            f"Output:"
        )

        try:
            resp = self.client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0,
                messages=[
                    {"role": "system", "content": REWRITE_PROMPT},
                    {"role": "user", "content": rewrite_input},
                ],
            )
            rewritten = resp.choices[0].message.content.strip()
            # Strip surrounding quotes if the model added them
            rewritten = rewritten.strip('"').strip("'").strip()
            return rewritten or question
        except Exception:
            return question

    # ---------- Context building ----------

    def _build_context(self, hits: dict) -> tuple[str, list[Source]]:
        docs = hits["documents"]
        metas = hits["metadatas"]
        dists = hits["distances"]

        parts, sources = [], []
        for doc, meta, dist in zip(docs, metas, dists):
            src_name = meta["source"].replace("\\", "/").split("/")[-1]
            page = meta["page"]
            parts.append(f"[Source: {src_name}, p.{page}]\n{doc}")
            sources.append(
                Source(
                    source=meta["source"],
                    page=page,
                    distance=float(dist),
                    snippet=doc[:200].replace("\n", " ") + ("..." if len(doc) > 200 else ""),
                )
            )
        return "\n\n---\n\n".join(parts), sources

    # ---------- Main ask ----------

    def ask(
        self,
        question: str,
        k: int = TOP_K,
        history: list[dict] | None = None,
    ) -> Answer:
        """
        history: list of {"role": "user"|"assistant", "text": str}
                 Pass previous turns to enable conversational follow-ups.
        """
        history = history or []

        # Step 1: rewrite if this is a follow-up
        rewritten = self._rewrite_query(question, history)

        # Step 2: retrieve using the rewritten (standalone) query
        hits = self.store.search(rewritten, k=k)

        if not hits["documents"]:
            return Answer(
                text="I don't know based on the provided documents.",
                sources=[],
                refused=True,
                rewritten_question=rewritten,
            )

        if hits["distances"] and hits["distances"][0] > SIMILARITY_THRESHOLD:
            return Answer(
                text="I don't know based on the provided documents.",
                sources=[],
                refused=True,
                rewritten_question=rewritten,
            )

        context, sources = self._build_context(hits)

        # Step 3: build the LLM message list with chat history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Include the last 4 turns of chat history (2 user + 2 assistant)
        for turn in history[-4:]:
            messages.append({
                "role": turn["role"],
                "content": turn["text"],
            })

        # Current question with context injected
        user_msg = (
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION: {rewritten}\n\n"
            "Answer using only the context above. Cite sources as [filename, p.X]."
        )
        messages.append({"role": "user", "content": user_msg})

        resp = self.client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            messages=messages,
        )
        answer = resp.choices[0].message.content.strip()
        refused = "i don't know based on the provided documents" in answer.lower()

        return Answer(
            text=answer,
            sources=[] if refused else sources,
            refused=refused,
            rewritten_question=rewritten,
        )


# ---------- Helpers ----------

def _looks_like_followup(q: str) -> bool:
    """Heuristic: does this question reference a prior turn?"""
    q_lower = q.lower().strip()
    triggers = [
        "what about", "how about", "and in", "and for",
        "what if", "explain more", "tell me more",
        "elaborate", "why is that", "why does that",
        "can you expand", "and why", "then what",
    ]
    if any(q_lower.startswith(t) for t in triggers):
        return True
    # Very short questions with pronouns often follow up
    if len(q_lower.split()) <= 4 and any(
        w in q_lower for w in [" it", " that", " this", " those", " them", " they"]
    ):
        return True
    return False


# ---------- CLI ----------

def _print_result(result: Answer) -> None:
    print("\n=== ANSWER ===")
    print(result.text)
    if result.sources:
        print("\n=== SOURCES ===")
        seen = set()
        for s in result.sources:
            key = (s.source, s.page)
            if key in seen:
                continue
            seen.add(key)
            print(f"  - {s.source}  (p.{s.page}, distance={s.distance:.3f})")


def interactive_cli(engine: RAGEngine, speak_flag: bool, voice: str | None, rate: int):
    """Interactive chat loop that remembers history."""
    print("Doc Assistant — interactive chat")
    print("Type your questions. Commands: /exit, /clear, /history")
    print()

    history: list[dict] = []

    while True:
        try:
            q = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not q:
            continue
        if q in ("/exit", "/quit", ":q"):
            break
        if q == "/clear":
            history = []
            print("[history cleared]")
            continue
        if q == "/history":
            for t in history:
                print(f"  {t['role']}: {t['text'][:100]}")
            continue

        result = engine.ask(q, history=history)
        _print_result(result)

        # Add to history
        history.append({"role": "user", "text": q})
        history.append({"role": "assistant", "text": result.text})

        if speak_flag and not result.refused:
            from speak import speak, speak_with_voice, list_voices
            voice_id = None
            if voice:
                for v in list_voices():
                    if voice.lower() in v["name"].lower():
                        voice_id = v["id"]
                        break
            if voice_id:
                speak_with_voice(result.text, voice_id, rate=rate, block=True)
            else:
                speak(result.text, rate=rate, block=True)


def main():
    parser = argparse.ArgumentParser(description="Ask questions about your documents.")
    parser.add_argument("question", nargs="*", help="Question (omit for interactive chat)")
    parser.add_argument("--speak", action="store_true", help="Read answers aloud")
    parser.add_argument("--voice", type=str, default="Microsoft Zira Desktop")
    parser.add_argument("--rate", type=int, default=175)
    parser.add_argument("--list-voices", action="store_true")
    args = parser.parse_args()

    if args.list_voices:
        from speak import list_voices
        for v in list_voices():
            print(f"  {v['name']}\n    id: {v['id']}\n")
        return

    engine = RAGEngine()

    if not args.question:
        # No question given → interactive chat with memory
        interactive_cli(engine, args.speak, args.voice, args.rate)
        return

    # Single-shot mode (no history)
    question = " ".join(args.question)
    result = engine.ask(question)
    _print_result(result)

    if args.speak and not result.refused:
        from speak import speak, speak_with_voice, list_voices
        voice_id = None
        if args.voice:
            for v in list_voices():
                if args.voice.lower() in v["name"].lower():
                    voice_id = v["id"]
                    break
        if voice_id:
            speak_with_voice(result.text, voice_id, rate=args.rate, block=True)
        else:
            speak(result.text, rate=args.rate, block=True)


if __name__ == "__main__":
    main()