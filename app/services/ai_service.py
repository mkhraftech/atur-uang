from google import genai
from google.genai import types
from PIL import Image
import json
import os
from datetime import datetime
from app.core.config import get_settings
from app.schemas.ai import ReceiptData
from app.core.logger import logger
from app.core.prompts import TRANSACTION_PARSER_PROMPT, RECEIPT_PARSER_PROMPT, TODO_REMINDER_PROMPT
import httpx

settings = get_settings()

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    async def parse_receipt(self, file_path: str) -> dict:
        """
        Parses a receipt image using Google Gemini AI with Structured Output.
        """
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_api_key_here":
            raise ValueError("GEMINI_API_KEY is not configured. Please add it to your .env file.")

        try:
            img = Image.open(file_path)
            
            prompt = RECEIPT_PARSER_PROMPT
            
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
        if user_now is None: user_now = datetime.now()
        now_str = user_now.strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = TRANSACTION_PARSER_PROMPT.format(text=text, now_str=now_str)

        try:
            response = self.client.models.generate_content(
                model=self.model_name, 
                contents=[prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text.strip())
        except Exception as e:
            logger.warning(f"Gemini failed, using Groq: {e}")
            return await self._call_fallback_groq(prompt, now_str, text)

    async def _make_groq_request(self, prompt: str) -> str:
        """Helper to make a Groq API request with robust error handling."""
        if not settings.GROQ_API_KEY:
            return None
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=15.0)
                
                if response.status_code != 200:
                    logger.error(f"Groq API returned error {response.status_code}: {response.text}")
                    return None
                
                resp_json = response.json()
                if 'choices' not in resp_json or not resp_json['choices']:
                    logger.error(f"Groq API response missing 'choices': {resp_json}")
                    return None
                
                return resp_json['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Failed to call Groq API: {e}", exc_info=True)
            return None

    async def _call_fallback_groq(self, prompt: str, now_str: str, original_text: str) -> dict:
        content = await self._make_groq_request(prompt)
        if content:
            try:
                return json.loads(content)
            except Exception as e:
                logger.error(f"Failed to parse Groq response as JSON: {e}")
        
        return {"amount": None, "date": now_str, "description": original_text, "type": "expense"}

    async def parse_todo_reminder(self, text: str, user_now: datetime = None) -> dict:
        if user_now is None: user_now = datetime.now()
        now_str = user_now.strftime("%Y-%m-%d %H:%M")
        offset_str = user_now.strftime("%z") or "+00:00"
        if len(offset_str) == 5: offset_str = offset_str[:3] + ":" + offset_str[3:]

        prompt = TODO_REMINDER_PROMPT.format(
            text=text, 
            now_str=now_str, 
            offset_str=offset_str, 
            year=user_now.year
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name, 
                contents=[prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text.strip())
        except Exception as e:
            logger.warning(f"Gemini failed for todo, trying Groq fallback: {e}")
            return await self._call_fallback_todo_groq(prompt, text)

    async def _call_fallback_todo_groq(self, prompt: str, original_text: str) -> dict:
        content = await self._make_groq_request(prompt)
        if content:
            try:
                return json.loads(content)
            except Exception as e:
                logger.error(f"Failed to parse Groq todo response as JSON: {e}")
        
        return {"todo_text": original_text, "remind_at": None}


ai_service = AIService()
