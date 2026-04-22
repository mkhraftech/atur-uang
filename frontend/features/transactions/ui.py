import streamlit as st
from services.api_client import create_transaction
from datetime import date


def render():
    st.subheader("💸 Tambah Transaksi")

    col1, col2 = st.columns(2)

    with col1:
        account_id = st.text_input(
            "Account ID",
            value="660e8400-e29b-41d4-a716-446655440001"
        )

        amount = st.number_input("Jumlah", min_value=0)

        transaction_type = st.selectbox(
            "Tipe",
            ["expense", "income"]
        )

    with col2:
        description = st.text_input("Deskripsi")

        transaction_date = st.date_input(
            "Tanggal",
            value=date.today()
        )

        category_ids = st.text_input(
            "Category IDs (pisahkan dengan koma)",
            ""
        )

    if st.button("Simpan Transaksi"):
        try:
            category_list = [
                c.strip() for c in category_ids.split(",") if c.strip()
            ]

            payload = {
                "account_id": account_id,
                "amount": amount,
                "type": transaction_type,
                "description": description,
                "transaction_date": str(transaction_date),
                "category_ids": category_list
            }

            res = create_transaction(payload)

            if res.status_code in [200, 201]:
                st.success("✅ Transaksi berhasil disimpan")
                st.json(res.json())
            else:
                st.error(f"❌ Error {res.status_code}")
                st.json(res.text)

        except Exception as e:
            st.error(f"Terjadi error: {e}")