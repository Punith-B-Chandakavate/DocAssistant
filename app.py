import re
from pathlib import Path
import tempfile

import streamlit as st

from config import DATA_DIR, SUPPORTED_EXTENSIONS
from vectorstore import VectorStore
from rag import RAGEngine
from ingest import ingest_file
from speak import speak, speak_with_voice, list_voices

st.set_page_config(page_title="Doc Assistant", page_icon="📚", layout="wide")


# ---------- Cached resources ----------
@st.cache_resource
def get_store():
    return VectorStore()


@st.cache_resource
def get_engine():
    return RAGEngine(store=get_store())


@st.cache_resource
def get_voices():
    return list_voices()


store = get_store()
engine = get_engine()
voices = get_voices()

if "history" not in st.session_state:
    st.session_state.history = []  # list of {role, text, sources, refused}

if "speak_counter" not in st.session_state:
    # Incrementing ID so each click triggers a distinct Streamlit event
    st.session_state.speak_counter = 0


# ---------- Helpers ----------
def render_sources(sources):
    if not sources:
        return
    with st.expander(f"📎 {len(sources)} source(s)"):
        seen = set()
        for s in sources:
            key = (s.source, s.page)
            if key in seen:
                continue
            seen.add(key)
            st.markdown(
                f"**{Path(s.source).name}** — page {s.page} "
                f"(distance {s.distance:.3f})"
            )
            st.caption(s.snippet)


def speak_text(text: str):
    """Called when the speaker button is clicked."""
    if not text or not text.strip():
        return
    voice_id = st.session_state.get("selected_voice_id")
    rate = st.session_state.get("voice_rate", 175)
    if voice_id:
        speak_with_voice(text, voice_id, rate=rate, block=False)
    else:
        speak(text, rate=rate, block=False)


# ---------- Sidebar ----------
with st.sidebar:
    st.title("📚 Doc Assistant")
    st.caption(f"Indexed chunks: **{store.count()}**")

    # --- Upload ---
    st.subheader("Upload")
    uploaded = st.file_uploader(
        "Add documents to your library",
        type=[e.lstrip(".") for e in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
    )
    if uploaded:
        for uf in uploaded:
            suffix = Path(uf.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uf.getbuffer())
                tmp_path = Path(tmp.name)
            dest = DATA_DIR / uf.name
            dest.write_bytes(tmp_path.read_bytes())
            with st.spinner(f"Ingesting {uf.name}..."):
                n = ingest_file(store, dest)
            if n:
                st.success(f"Added {n} chunks from {uf.name}")
            else:
                st.info(f"{uf.name}: no new chunks (already indexed or empty)")

    # --- Library ---
    st.divider()
    st.subheader("Library")
    sources = store.list_sources()
    if sources:
        for s in sources:
            st.write(f"📄 {Path(s).name}")
    else:
        st.write("_No documents yet._")

    # --- Voice settings (always visible — no toggle) ---
    st.divider()
    st.subheader("🔊 Voice Settings")

    if voices:
        voice_names = [v["name"] for v in voices]
        # Default to Zira if present, else first
        default_idx = next(
            (i for i, n in enumerate(voice_names) if "Zira" in n),
            0,
        )
        chosen = st.selectbox("Voice", voice_names, index=default_idx)
        st.session_state.selected_voice_id = next(
            (v["id"] for v in voices if v["name"] == chosen), None
        )
    else:
        st.warning("No voices detected on this system.")
        st.session_state.selected_voice_id = None

    st.session_state.voice_rate = st.slider(
        "Speed (words/min)", 120, 240, 175, 5
    )

    if st.button("🔈 Test voice"):
        test_text = "This is how I will read your answers."
        speak_text(test_text)

    # --- Actions ---
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()
    with col2:
        if st.button("🧹 Clear chat"):
            st.session_state.history = []
            st.rerun()
    with col3:
        if st.button("🗑️ Reset DB"):
            store.reset()
            st.session_state.history = []
            st.success("Cleared.")
            st.rerun()


# ---------- Main ----------
st.title("Ask your documents")

# Replay chat history with a speaker button on every assistant message
for i, turn in enumerate(st.session_state.history):
    with st.chat_message(turn["role"]):
        st.markdown(turn["text"])

        if turn["role"] == "assistant":
            # Speaker button + copy of sources
            cols = st.columns([1, 8])
            with cols[0]:
                # Unique key per message so Streamlit doesn't confuse them
                if st.button("🔊", key=f"speak_hist_{i}", help="Read this answer aloud"):
                    speak_text(turn["text"])
            with cols[1]:
                pass  # keep layout tidy

            render_sources(turn.get("sources", []))


# Input
question = st.chat_input("Ask a question about your documents...")

if question:
    # Add and render user message
    st.session_state.history.append({"role": "user", "text": question, "sources": []})
    with st.chat_message("user"):
        st.markdown(question)

    # Generate assistant answer
    with st.chat_message("assistant"):
        with st.spinner("Searching and generating..."):
            # Convert session history to the format ask() expects
            prior_turns = [
                {"role": t["role"], "text": t["text"]}
                for t in st.session_state.history
                if t["role"] in ("user", "assistant")
            ]
            result = engine.ask(question, history=prior_turns)

        st.markdown(result.text)

        # Speaker button for this fresh answer
        if not result.refused:
            if st.button("🔊 Speak this answer", key=f"speak_new_{len(st.session_state.history)}"):
                speak_text(result.text)

        render_sources(result.sources)

    st.session_state.history.append({
        "role": "assistant",
        "text": result.text,
        "sources": result.sources,
        "refused": result.refused,
    })