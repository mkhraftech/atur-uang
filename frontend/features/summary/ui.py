import streamlit as st
from services.api_client import get_summary


def render():
    st.subheader("Ringkasan")

    res = get_summary()

    if res.status_code == 200:
        data = res.json()

        st.metric("Total Pengeluaran", data["total_expense"])
        st.metric("Saldo", data["balance"])