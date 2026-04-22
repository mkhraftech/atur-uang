from google import genai
from google.genai import types
from PIL import Image
import json
import os
from datetime import datetime
from app.core.config import get_settings
from app.schemas.ai import ReceiptData

settings = get_settings()

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = 'gemini-1.5-flash'

    async def parse_receipt(self, file_path: str) -> dict:
        """
        Parses a receipt image using Google Gemini AI with Structured Output.
        """
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_api_key_here":
            raise ValueError("GEMINI_API_KEY is not configured. Please add it to your .env file.")

        try:
            img = Image.open(file_path)
            
            prompt = """
            Analyze this receipt and extract information accurately into a JSON format.
            Focus on Indonesian receipts if applicable (look for keywords like 'Total', 'Jumlah', 'Bayar', 'Kembalian').
            
            Output MUST be a valid JSON with these fields:
            - amount: (number) The FINAL total amount paid. Ignore taxes if they are already included in the total.
            - date: (string, YYYY-MM-DD) The date of the transaction.
            - merchant: (string) The name of the store, brand, or service provider.
            - description: (string) A readable summary of the purchase (e.g., 'Lunch at KFC', 'Groceries at Indomaret').
            - category_suggestion: (string) A suggested category like 'Food', 'Transport', 'Shopping', 'Health', 'Bills'.
            - items: (list of strings) Brief names of individual items bought.
            - currency: (string) Three-letter currency code, default to 'IDR'.

            Rules:
            1. If information is missing, use null for numbers or empty strings for text.
            2. For the date, if year is missing, assume the current year (2025).
            3. Return ONLY the JSON object.
            """
            
            # Using generation_config to force JSON output
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, img],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            # Parse the JSON response
            raw_text = response.text.strip()
            data_dict = json.loads(raw_text)
            
            # Use Pydantic to validate and provide default values
            receipt_data = ReceiptData(**data_dict)
            
            # Fallback for date if missing
            if not receipt_data.transaction_date:
                receipt_data.transaction_date = datetime.now().date()
            
            # Use by_alias=True to ensure the key is 'date' not 'transaction_date'
            return receipt_data.model_dump(by_alias=True)
            
        except Exception as e:

            print(f"Error in AIService.parse_receipt: {str(e)}")
            # Return a basic fallback if AI fails
            return {
                "amount": None,
                "date": str(datetime.now().date()),
                "merchant": "Unknown Merchant",
                "description": "Receipt parsing failed",
                "category_suggestion": "Others",
                "items": [],
                "currency": "IDR",
                "error": str(e)
            }

    async def parse_transaction_text(self, text: str) -> dict:
        """
        Parses a natural language transaction text using Google Gemini AI.
        """
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_api_key_here":
            raise ValueError("GEMINI_API_KEY is not configured.")

        try:
            prompt = f"""
            Extract transaction details from this text accurately into a JSON format.
            Text: "{text}"
            
            Focus on Indonesian context and currency (e.g., 'rb' means '000').
            
            Output MUST be a valid JSON with these fields:
            - amount: (number) The total amount spent or received.
            - date: (string, YYYY-MM-DD) The date of the transaction. Default to today ({datetime.now().date()}).
            - merchant: (string) The name of the store or person involved.
            - description: (string) A short summary of the transaction.
            - category_suggestion: (string) Choose ONE that fits best from: 'Wajib', 'Harian', 'Jajan', 'Transport', 'Impulsif'. Default to 'Jajan' if unsure.
            - currency: (string) Default to 'IDR'.

            Rules:
            1. If it sounds like an income, mark it as such in the description but provide the amount as positive.
            2. For amounts like '50rb', '50k', parse as 50000.
            3. Return ONLY the JSON object.
            """
            
            print(f"DEBUG AI PROMPT: {prompt}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            raw_text = response.text.strip()
            print(f"DEBUG AI RAW RESPONSE: {raw_text}")
            data_dict = json.loads(raw_text)
            
            receipt_data = ReceiptData(**data_dict)
            
            if not receipt_data.transaction_date:
                receipt_data.transaction_date = datetime.now().date()
            
            return receipt_data.model_dump(by_alias=True)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error in AIService.parse_transaction_text: {str(e)}")
            return {
                "amount": None,
                "date": str(datetime.now().date()),
                "merchant": "Unknown",
                "description": text,
                "category_suggestion": "Others",
                "currency": "IDR"
            }

ai_service = AIService()
