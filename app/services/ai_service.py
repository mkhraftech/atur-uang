from google import genai
from google.genai import types
from PIL import Image
import json
import os
from datetime import datetime
from app.core.config import get_settings
from app.schemas.ai import ReceiptData
from app.core.logger import logger

settings = get_settings()

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = 'gemini-2.5-flash'

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
            - type: (string) Either 'expense' or 'income'. Default to 'expense'.

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
            logger.error(f"Error in AIService.parse_receipt: {str(e)}", exc_info=True)
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

    async def parse_transaction_text(self, text: str, user_now: datetime = None) -> dict:
        """
        Parses a natural language transaction text using Google Gemini AI.
        """
        if user_now is None:
            user_now = datetime.now()
        
        now_str = user_now.strftime("%Y-%m-%d")
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_api_key_here":
            raise ValueError("GEMINI_API_KEY is not configured.")

        try:
            prompt = f"""
            Extract transaction details from this text accurately into a JSON format.
            Text: "{text}"
            
            Focus on Indonesian context and currency (e.g., 'rb' means '000').
            
            Output MUST be a valid JSON with these fields:
            - amount: (number) The total amount spent or received.
            - date: (string, YYYY-MM-DD) The date of the transaction. Default to today ({now_str}).
            - merchant: (string) The name of the store or person involved.
            - description: (string) A short summary of the transaction.
            - category_suggestion: (string) Choose ONE that fits best from: 'Wajib', 'Harian', 'Jajan', 'Transport', 'Impulsif'. Default to 'Jajan' if unsure.
            - currency: (string) Default to 'IDR'.
            - type: (string) Either 'expense' or 'income'. Detect this from context.

            Rules:
            1. For amounts like '50rb', '50k', parse as 50000.
            2. Return ONLY the JSON object.
            """
            
            logger.debug(f"AI PROMPT: {prompt}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            raw_text = response.text.strip()
            logger.debug(f"AI RAW RESPONSE: {raw_text}")
            data_dict = json.loads(raw_text)
            
            receipt_data = ReceiptData(**data_dict)
            
            if not receipt_data.transaction_date:
                receipt_data.transaction_date = datetime.now().date()
            
            return receipt_data.model_dump(by_alias=True)
            
        except genai.errors.ServerError as e:
            prompt = f"""
            Extract transaction details from this text accurately into a JSON format.
            Text: "{text}"
            
            Focus on Indonesian context and currency (e.g., 'rb' means '000').
            
            Output MUST be a valid JSON with these fields:
            - amount: (number) The total amount spent or received.
            - date: (string, YYYY-MM-DD) The date of the transaction. Default to today ({now_str}).
            - merchant: (string) The name of the store or person involved.
            - description: (string) A short summary of the transaction.
            - category_suggestion: (string) Choose ONE that fits best from: 'Wajib', 'Harian', 'Jajan', 'Transport', 'Impulsif'. Default to 'Jajan' if unsure.
            - currency: (string) Default to 'IDR'.
            - type: (string) Either 'expense' or 'income'. Detect this from context.

            Rules:
            1. For amounts like '50rb', '50k', parse as 50000.
            2. Return ONLY the JSON object.
            """
            
            logger.debug(f"AI PROMPT: {prompt}")
            response = self.client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            raw_text = response.text.strip()
            logger.debug(f"AI RAW RESPONSE: {raw_text}")
            data_dict = json.loads(raw_text)
            
            receipt_data = ReceiptData(**data_dict)
            
            if not receipt_data.transaction_date:
                receipt_data.transaction_date = datetime.now().date()
            
            return receipt_data.model_dump(by_alias=True)
        except Exception as e:
            logger.exception(f"Error in AIService.parse_transaction_text: {str(e)}")
            return {
                "amount": None,
                "date": str(datetime.now().date()),
                "merchant": "Unknown",
                "description": text,
                "category_suggestion": "Others",
                "currency": "IDR"
            }

    async def parse_todo_reminder(self, text: str, user_now: datetime = None) -> dict:
        """
        Parse pesan todo/reminder dari teks natural.
        Return: { "todo_text": str, "remind_at": "YYYY-MM-DDTHH:MM:SS+07:00" | null }
        """
        if user_now is None:
            user_now = datetime.now()
            
        try:
            now_str = user_now.strftime("%Y-%m-%d %H:%M")
            offset_str = user_now.strftime("%z") or "+00:00"
            # Ensure format is +HH:MM
            if len(offset_str) == 5:
                offset_str = offset_str[:3] + ":" + offset_str[3:]

            prompt = f"""
            Ekstrak informasi todo/reminder dari teks berikut dalam konteks Bahasa Indonesia.
            Teks: "{text}"
            Waktu sekarang: {now_str} (Offset {offset_str})

            Output MUST be valid JSON with:
            - todo_text: (string) isi todo/pengingat yang singkat dan jelas
            - remind_at: (string | null) waktu reminder dalam format ISO 8601 dengan offset {offset_str} (contoh: 2025-04-26T09:00:00{offset_str}).
              PENTING: Gunakan tahun {user_now.year} jika tidak disebutkan.
              Null jika tidak ada waktu yang disebutkan.

            Contoh:
            - "ingatkan besok jam 9 pagi" → remind_at: (besok)T09:00:00+07:00
            - "todo: beli susu"           → remind_at: null
            - "remind me in 2 hours"      → remind_at: (sekarang + 2 jam)T(HH:MM:SS)+07:00

            Return ONLY the JSON object.
            """
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            data = json.loads(response.text.strip())
            logger.debug(f"parse_todo_reminder result: {data}")
            return data
        except Exception as e:
            logger.exception(f"Error in parse_todo_reminder: {e}")
            # Fallback: anggap todo biasa tanpa reminder
            return {"todo_text": text, "remind_at": None}


ai_service = AIService()
