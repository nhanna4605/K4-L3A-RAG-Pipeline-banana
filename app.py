"""Streamlit chat with persistent answers and inspectable sources."""

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation

load_dotenv()
st.set_page_config(page_title="RAG Chatbot", page_icon="📚", layout="wide")


def show_sources(message: dict) -> None:
    st.caption(f"Nguồn truy xuất: {message.get('retrieval_source', 'none')}")
    for index, source in enumerate(message.get("sources", []), 1):
        metadata = source["metadata"]
        with st.expander(f"[{index}] {metadata['title']}"):
            st.text(f"Nguồn: {metadata['source']}")
            st.caption(f"ID: {source['id']} · {source['retrieval_method']} · Score: {source['score']:.4f}")
            url = metadata.get("url")
            if url and url.startswith(("https://", "http://")):
                st.link_button("Mở tài liệu gốc", url)
            st.text(source["content"])


if "messages" not in st.session_state:
    st.session_state.messages = []
with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Hỏi đáp dựa trên bộ tài liệu của nhóm")
    top_k = st.slider("Số chunks", 3, 10, 5)
    if st.button("Xóa hội thoại"):
        st.session_state.messages = []
        st.rerun()
st.title("Hỏi đáp tài liệu")
st.caption("Đặt câu hỏi và mở các nguồn bên dưới để kiểm chứng câu trả lời.")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            show_sources(message)
query = st.chat_input("Nhập câu hỏi...")
if query and query.strip():
    query = query.strip()
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm tài liệu và tạo câu trả lời..."):
            result = generate_with_citation(query, top_k=top_k)
        message = {"role": "assistant", "content": result["answer"],
                   "sources": result["sources"], "retrieval_source": result["retrieval_source"]}
        st.markdown(message["content"])
        show_sources(message)
    st.session_state.messages.append(message)
