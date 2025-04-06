"""streamlit chat UI with day-by-day itinerary panel."""
from __future__ import annotations

import os

import streamlit as st

from src.graph import run as run_graph
from src.llm import llm_from_env
from src.state import Itinerary

st.set_page_config(page_title="Travel Planner", layout="wide")
st.title("multi-agent travel planner")

if "history" not in st.session_state:
    st.session_state.history = []
if "itinerary" not in st.session_state:
    st.session_state.itinerary = None

left, right = st.columns([1, 1])

with left:
    st.subheader("chat")
    for role, text in st.session_state.history:
        with st.chat_message(role):
            st.markdown(text)

    user_msg = st.chat_input("describe your trip in plain words")
    if user_msg:
        st.session_state.history.append(("user", user_msg))
        with st.spinner("agents are planning..."):
            llm = llm_from_env()
            try:
                it: Itinerary = run_graph(user_msg, llm=llm)
                st.session_state.itinerary = it
                st.session_state.history.append(
                    ("assistant", it.summary or "done")
                )
            except Exception as e:
                st.session_state.history.append(("assistant", f"error: {e}"))
        st.rerun()

with right:
    st.subheader("itinerary")
    it = st.session_state.itinerary
    if it is None:
        st.info("no itinerary yet")
    else:
        st.write(f"**summary**: {it.summary}")
        st.write(f"**budget**: {it.budget.total} {it.budget.currency} (over: {it.budget.over_budget})")
        if it.flights:
            f = it.flights[0]
            st.write(f"**flight**: {f.carrier}{f.flight_number} {f.depart_iata}->{f.arrive_iata} {f.depart_at} ({f.price} {f.currency})")
        if it.hotel:
            st.write(f"**hotel**: {it.hotel.name} ({it.hotel.price_per_night} {it.hotel.currency}/night)")
        if it.days:
            tabs = st.tabs([f"day {d.day_index}" for d in it.days])
            for tab, d in zip(tabs, it.days):
                with tab:
                    if d.weather:
                        st.write(f"weather: {d.weather.summary}, {d.weather.temp_c_min}-{d.weather.temp_c_max}C, rain {d.weather.precipitation_mm}mm")
                    if d.notes:
                        st.caption(d.notes)
                    st.markdown("**morning**")
                    for a in d.morning:
                        st.write(f"- {a.name} ({a.duration_hours}h, {a.price} {it.budget.currency})")
                    st.markdown("**afternoon**")
                    for a in d.afternoon:
                        st.write(f"- {a.name} ({a.duration_hours}h, {a.price} {it.budget.currency})")
                    st.markdown("**evening**")
                    for a in d.evening:
                        st.write(f"- {a.name} ({a.duration_hours}h, {a.price} {it.budget.currency})")
                    st.caption(f"day cost: {d.estimated_cost} {it.budget.currency}")
