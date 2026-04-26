
import uuid
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.category import Category
from app.models.category_rule import CategoryRule
from datetime import datetime

def seed_data():
    db: Session = SessionLocal()
    print("🚀 Memulai seeding data...")

    # 1. DAFTAR KATEGORI DASAR
    # Format: (Nama, Tipe)
    categories_to_seed = [
        # Pengeluaran
        ("Wajib", "expense"),
        ("Kebutuhan Pokok", "expense"),
        ("Jajan", "expense"),
        ("Transport", "expense"),
        ("Impulsif", "expense"),
        ("Kesehatan", "expense"),
        ("Pendidikan", "expense"),
        ("Lainnya", "expense"),
        # Pemasukan
        ("Gaji", "income"),
        ("Bonus", "income"),
        ("Piutang", "income"),
    ]

    category_map = {}

    for name, cat_type in categories_to_seed:
        # Cek apakah kategori sudah ada
        existing = db.query(Category).filter(Category.name == name, Category.type == cat_type).first()
        if not existing:
            new_cat = Category(
                id=uuid.uuid4(),
                name=name,
                type=cat_type,
                created_at=datetime.now()
            )
            db.add(new_cat)
            db.flush()
            category_map[name] = new_cat
            print(f"✅ Kategori dibuat: {name} ({cat_type})")
        else:
            category_map[name] = existing
            print(f"ℹ️ Kategori sudah ada: {name}")

    # 2. DAFTAR ATURAN KATA KUNCI (RULES)
    # Format: (Keyword, Nama Kategori)
    rules_to_seed = [
        # Transport
        ("bensin", "Transport"),
        ("pertalite", "Transport"),
        ("pertamax", "Transport"),
        ("gojek", "Transport"),
        ("grab", "Transport"),
        ("parkir", "Transport"),
        ("tol", "Transport"),
        
        # Jajan
        ("kopi", "Jajan"),
        ("starbucks", "Jajan"),
        ("ngopi", "Jajan"),
        ("snack", "Jajan"),
        ("boba", "Jajan"),
        ("mixue", "Jajan"),
        ("film", "Jajan"),
        ("netflix", "Jajan"),

        # Kebutuhan Pokok
        ("makan", "Kebutuhan Pokok"),
        ("nasi", "Kebutuhan Pokok"),
        ("warteg", "Kebutuhan Pokok"),
        ("sayur", "Kebutuhan Pokok"),
        ("beras", "Kebutuhan Pokok"),
        ("galon", "Kebutuhan Pokok"),
        ("sabun", "Kebutuhan Pokok"),
        ("odol", "Kebutuhan Pokok"),
        ("pasar", "Kebutuhan Pokok"),

        # Wajib
        ("listrik", "Wajib"),
        ("token", "Wajib"),
        ("wifi", "Wajib"),
        ("indihome", "Wajib"),
        ("kontrakan", "Wajib"),
        ("kos", "Wajib"),
        ("cicilan", "Wajib"),
        ("asuransi", "Wajib"),
        ("bpjs", "Wajib"),

        # Pemasukan
        ("gaji", "Gaji"),
        ("bonus", "Bonus"),
        ("thr", "Bonus"),
        ("refund", "Bonus"),
    ]

    for keyword, cat_name in rules_to_seed:
        target_cat = category_map.get(cat_name)
        if target_cat:
            # Cek apakah rule sudah ada
            existing_rule = db.query(CategoryRule).filter(
                CategoryRule.keyword == keyword, 
                CategoryRule.category_id == target_cat.id
            ).first()
            
            if not existing_rule:
                new_rule = CategoryRule(
                    id=uuid.uuid4(),
                    category_id=target_cat.id,
                    keyword=keyword,
                    created_at=datetime.now()
                )
                db.add(new_rule)
                print(f"🔹 Rule dibuat: '{keyword}' -> {cat_name}")

    try:
        db.commit()
        print("\n✨ Seeding selesai dengan sukses!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error saat seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Pastikan tabel sudah dibuat
    # Base.metadata.create_all(bind=engine)
    seed_data()
