"""Minimal Streamlit chat UI for the discovery engine."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from productpilot.discovery.service import DiscoveryEngineService

service = DiscoveryEngineService(Path(__file__).resolve().parents[3])

st.set_page_config(page_title="Myntra Wishlist Discovery", page_icon="🛍️")
st.title("Myntra Wishlist Discovery Engine")
st.caption("Grounded answers only. Monetary incentives are filtered out.")

question = st.text_input("Ask a question", placeholder="What's the top friction point for footwear under ₹2000?")
if st.button("Ask") and question:
    answer = service.answer(question)
    st.subheader("Answer")
    st.write(answer["answer_text"])
    st.write(f"Confidence tier: {answer['confidence_tier']}")
    if answer.get("out_of_scope_notice"):
        st.warning(answer["out_of_scope_notice"])
    with st.expander("Citations"):
        for citation in answer["citations"]:
            st.markdown(f"- [{citation['url']}]({citation['url']}) — {citation['snippet']}")
    feedback = st.radio("Feedback", ["up", "down"], horizontal=True)
    correction = st.text_input("Optional correction")
    if st.button("Save feedback"):
        service.store.log_chat(question, [], answer["answer_text"], feedback=feedback, correction=correction or None)
        st.success("Feedback saved")
