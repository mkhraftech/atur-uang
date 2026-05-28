
# Prompt for Transaction Parsing
TRANSACTION_PARSER_PROMPT = """
Extract transaction details from this text accurately into a JSON format.
If the text contains multiple transactions (e.g. lists, bullet points, numbered lists, or multiple separate items), detect all of them and return them as a list under the "transactions" key.
Text: "{text}"
Today is: {now_str} (format YYYY-MM-DD HH:MM:SS)

Focus on Indonesian context and currency (e.g., 'rb' means '000').

Output MUST be a valid JSON with this format:
{{
  "transactions": [
    {{
      "amount": (number) The total amount.
      "date": (string, YYYY-MM-DD HH:MM:SS) Default to current time ({now_str}).
      "merchant": (string)
      "description": (string)
      "category_suggestion": (string) Choose ONE from categories below.
      "currency": (string) Default 'IDR'.
      "type": (string) 'expense' or 'income'.
    }}
  ]
}}

Categories & Definitions:
- 'Wajib': Pembayaran hutang, cicilan, asuransi, pajak, biaya sekolah.
- 'Kebutuhan Pokok': Sembako, makan rutin, listrik, air, pulsa/data, internet.
- 'Kebutuhan Non-Rutin': Pembelian besar yang perlu tapi tidak rutin (Beli AC, perbaikan rumah, biaya RS, servis besar).
- 'Transport': Bensin, parkir, ojek online, tiket transportasi.
- 'Jajan': Makan di luar, kopi, bioskop, hiburan.
- 'Piutang': Menghutangi atau meminjamkan uang kepada orang lain.
- 'Impulsif': Belanja hobi, barang yang tidak direncanakan, atau keinginan semata.

Rules:
1. For amounts like '50rb', '50k', parse as 50000.
2. Return ONLY the JSON object.
3. If the user input lists multiple items (e.g. using bullet points, numbers, or new lines), extract each item as a separate transaction in the "transactions" array.
4. Calculate the transaction date & time relative to today ({now_str}). For example:
   - "kemarin beli..." -> set date to yesterday's date, preserving current time or using the time if specified.
   - "kemarin jam 7 malam..." -> set date-time to yesterday at 19:00:00.
   - "tadi pagi jam 8..." -> set date-time to today at 08:00:00.
   - "2 jam lalu..." -> subtract 2 hours from the current time.
   - If no date/time is mentioned, default to current time ({now_str}).
"""

# Prompt for Receipt/Image Parsing
RECEIPT_PARSER_PROMPT = """
Analyze this receipt and extract information accurately into a JSON format.
Focus on Indonesian receipts if applicable (look for keywords like 'Total', 'Jumlah', 'Bayar', 'Kembalian').

Output MUST be a valid JSON with these fields:
- amount: (number) The FINAL total amount paid.
- date: (string, YYYY-MM-DD) The date of the transaction.
- merchant: (string)
- description: (string)
- category_suggestion: (string) Choose ONE: 'Wajib', 'Kebutuhan Pokok', 'Kebutuhan Non-Rutin', 'Transport', 'Jajan', 'Impulsif'.
- items: (list of strings)
- currency: (string) Default 'IDR'.
- type: (string) 'expense' or 'income'.

Rules:
1. If information is missing, use null for numbers or empty strings for text.
2. Return ONLY the JSON object.
"""

# Prompt for Todo and Reminder Parsing
TODO_REMINDER_PROMPT = """
Ekstrak informasi todo/reminder dari teks berikut dalam konteks Bahasa Indonesia.
Teks: "{text}"
Waktu sekarang: {now_str} (Offset {offset_str})

Output MUST be valid JSON with:
- todo_text: (string) isi todo/pengingat yang singkat dan jelas
- remind_at: (string | null) waktu reminder dalam format ISO 8601 dengan offset {offset_str}.
  Gunakan tahun {year} jika tidak disebutkan.

Return ONLY the JSON object.
"""

# Prompt for Chat Intent Routing
INTENT_ROUTER_PROMPT = """
Analyze the following user chat message and determine the user's intent.
Text: "{text}"
Today is: {now_str} (format YYYY-MM-DD HH:MM:SS)

Classify the intent into ONE of these categories:
1. "summary": The user wants to see a financial summary/rekap. This includes queries for:
   - All time summary (e.g., "summary", "rekap keuangan", "saldo saya")
   - Specific periods (e.g., "hari ini", "kemarin", "bulan ini", "bulan lalu", "minggu ini", "2 hari lalu", "pengeluaran 3 hari terakhir", "pemasukan minggu lalu").
   For this intent, calculate the `start_date` and `end_date` relative to today ({now_str}) in 'YYYY-MM-DD' format. If it is all-time summary (not specifying a period), set both to null.
2. "list_todo": The user wants to view their todo list (e.g., "list todo", "daftar pengingat", "todo list").
3. "complete_todo": The user wants to mark a todo as done/completed (e.g., "done 3", "selesai 5", "todo 1 selesai"). Extract the integer ID as `todo_id`.
4. "delete_todo": The user wants to delete/remove a todo (e.g., "hapus 2", "delete 10", "del 4"). Extract the integer ID as `todo_id`.
5. "show_timezone": The user wants to check their timezone settings (e.g., "timezone", "cek zona waktu").
6. "set_timezone": The user wants to set/change their timezone (e.g., "set timezone Asia/Makassar"). Extract the timezone name as `timezone`.
7. "todo_reminder": The user wants to add a new todo or a reminder. This typically starts with keywords like "todo", "ingatkan", "remind", "reminder", "pengingat", or phrases like "ingatkan saya untuk...".
8. "record_transaction": The user wants to input/record transactions (e.g., "kopi 15rb", "gas 20k", "pemasukan gajian 5jt", "tadi pagi beli bensin 50rb"). If it does not match any of the above intents and looks like financial recording, classify as "record_transaction".

Output MUST be a valid JSON with this format:
{{
  "intent": "summary" | "list_todo" | "complete_todo" | "delete_todo" | "show_timezone" | "set_timezone" | "todo_reminder" | "record_transaction",
  "parameters": {{
    "start_date": (string, YYYY-MM-DD or null),
    "end_date": (string, YYYY-MM-DD or null),
    "todo_id": (integer or null),
    "timezone": (string or null)
  }}
}}

Return ONLY the JSON object.
"""
