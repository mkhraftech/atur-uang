import os
from fastapi import UploadFile
from app.services.ai_service import ai_service
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionCreate

UPLOAD_DIR = "uploads"


async def process_receipt(db, file: UploadFile, user):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = f"{UPLOAD_DIR}/{file.filename}"

    # save file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return await process_receipt_from_path(db, file_path, user)


async def process_receipt_from_path(db, file_path, user_id):
    # 🤖 AI Parsing (Structured Output)
    parsed_data = await ai_service.parse_receipt(file_path)

    amount = parsed_data.get("amount")
    date = parsed_data.get("date")
    merchant = parsed_data.get("merchant")
    description_raw = parsed_data.get("description")
    items = parsed_data.get("items", [])
    category_suggestion = parsed_data.get("category_suggestion")
    
    # Construct a rich description
    if merchant and items:
        description = f"{merchant}: {', '.join(items[:3])}"
        if len(items) > 3:
            description += "..."
    elif merchant and description_raw:
        description = f"{merchant}: {description_raw}"
    elif merchant:
        description = f"Belanja di {merchant}"
    else:
        description = description_raw or "Pembelian dari struk"

    # fallback for missing amount
    if not amount:
        return {
            "success": False,
            "error": "AI tidak berhasil menemukan total nominal di struk ini.",
            "data": parsed_data
        }

    # Prepare transaction data
    transaction_data = TransactionCreate(
        account_id="660e8400-e29b-41d4-a716-446655440001", 
        amount=amount,
        type="expense",
        description=description,
        transaction_date=date,
        category_ids=[], # Will be auto-detected by TransactionService if empty
        category_suggestion=category_suggestion
    )

    # Save to database using TransactionService
    transaction = TransactionService.create_transaction(db, user_id, transaction_data)

    return {
        "success": True,
        "message": "Berhasil memproses struk menggunakan AI",
        "data": {
            "id": str(transaction.id) if hasattr(transaction, 'id') else None,
            "amount": amount,
            "description": description,
            "date": date,
            "merchant": merchant,
            "items": items,
            "category_suggestion": category_suggestion
        }
    }