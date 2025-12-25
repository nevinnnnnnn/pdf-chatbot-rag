import json
import os
import streamlit as st
import pandas as pd
from datetime import datetime

ANALYTICS_FILE = "data/analytics/interactions.json"

st.set_page_config(
    page_title="PDF Chatbot Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PDF Chatbot – Analytics Dashboard")

# --- Load Analytics ---
if not os.path.exists(ANALYTICS_FILE):
    st.warning("No analytics data available yet.")
    st.stop()

with open(ANALYTICS_FILE, "r") as f:
    data = json.load(f)

if not data:
    st.warning("Analytics file is empty.")
    st.stop()

df = pd.DataFrame(data)

df["timestamp"] = pd.to_datetime(df["timestamp"])

# --- KPI Metrics ---
col1, col2 = st.columns(2)

col1.metric("Total Questions Asked", len(df))
col2.metric("Unique Questions", df["question"].nunique())

st.divider()

# --- Timeline ---
st.subheader("📈 Questions Over Time")

timeline = df.groupby(df["timestamp"].dt.date).size()
st.line_chart(timeline)

st.divider()

# --- Recent Questions ---
st.subheader("🕒 Recent Questions")

st.dataframe(
    df[["timestamp", "question"]]
    .sort_values(by="timestamp", ascending=False)
    .head(10),
    width="stretch"
)

st.divider()

# --- Question → Answer Viewer ---
st.subheader("🔍 Question Explorer")

selected = st.selectbox(
    "Select a question",
    df["question"].unique()
)

row = df[df["question"] == selected].iloc[-1]

st.markdown("### 🧠 Answer")
st.write(row["answer"])

st.markdown("### 📚 Sources")
if row["sources"]:
    for src in row["sources"]:
        st.write(f"Page {src['page']} (distance: {src['distance']})")
else:
    st.write("No sources logged.")