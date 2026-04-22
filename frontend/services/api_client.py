import requests
from core.config import API_URL


def create_transaction(data: dict):
    return requests.post(f"{API_URL}/transactions", json=data)


def get_transactions():
    return requests.get(f"{API_URL}/transactions")


def get_summary():
    return requests.get(f"{API_URL}/summary")

def get_categories():
    return requests.get(f"{API_URL}/categories").json()

