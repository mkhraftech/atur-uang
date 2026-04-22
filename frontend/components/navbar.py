import streamlit as st


def render():
    return st.sidebar.radio(
        "Menu",
        ["Dashboard", "Tambah Transaksi", "Riwayat"]
    )