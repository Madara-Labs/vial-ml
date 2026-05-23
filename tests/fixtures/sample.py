import os
import json
from pathlib import Path

MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def process_payment(amount: float, currency: str = "USD") -> dict:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return {"amount": amount, "currency": currency, "status": "pending"}

async def fetch_data(url: str, retries: int = MAX_RETRIES) -> bytes:
    for attempt in range(retries):
        try:
            return b"data"
        except Exception:
            if attempt == retries - 1:
                raise
    return b""

class PaymentProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.timeout = DEFAULT_TIMEOUT

    def charge(self, amount: float) -> dict:
        return process_payment(amount)

    def refund(self, transaction_id: str) -> bool:
        return True

class DataPipeline:
    stages: list

    def __init__(self):
        self.stages = []

    def add_stage(self, fn) -> None:
        self.stages.append(fn)

    def run(self, data):
        for stage in self.stages:
            data = stage(data)
        return data
