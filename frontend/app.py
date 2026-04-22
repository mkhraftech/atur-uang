import streamlit as st

from components.navbar import render as navbar
from features.transactions.ui import render as transaksi_ui
from features.summary.ui import render as summary_ui
from features.history.ui import render as history_ui


st.set_page_config(page_title="Atur Uang", layout="wide")

menu = navbar()

st.title("💰 Atur Uang")

if menu == "Dashboard":
    summary_ui()

elif menu == "Tambah Transaksi":
    transaksi_ui()

elif menu == "Riwayat":
    history_ui()