
# Prompt for Transaction Parsing
TRANSACTION_PARSER_PROMPT = """
Extract transaction details from this text accurately into a JSON format.
Text: "{text}"
Today is: {now_str}

Focus on Indonesian context and currency (e.g., 'rb' means '000').

Output MUST be a valid JSON with these fields:
- amount: (number) The total amount.
- date: (string, YYYY-MM-DD) Default to today ({now_str}).
- merchant: (string)
- description: (string)
- category_suggestion: (string) Choose ONE from categories below.
- currency: (string) Default 'IDR'.
- type: (string) 'expense' or 'income'.

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
