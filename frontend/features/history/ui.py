import streamlit as st
import json
from services.api_client import get_transactions


def render():
    st.subheader("Riwayat Transaksi")

    res = get_transactions()

    if res.status_code == 200:
        st.table(res.json())