import os
from sqlalchemy import text
from app import app, db

with app.app_context():
    os.makedirs("/app/data", exist_ok=True)
    db.create_all()

    # Migrações simples para bancos já existentes no volume do Coolify
    engine = db.engine
    with engine.begin() as conn:
        def columns(table):
            return {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}

        for table in ("work_order", "quote"):
            cols = columns(table)
            additions = {
                "vehicle_id": "INTEGER",
                "service_type": "VARCHAR(80) DEFAULT 'Elétrica automotiva'",
                "mileage": "VARCHAR(30) DEFAULT ''",
            }
            for name, ddl in additions.items():
                if name not in cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))

    print("JL Elétrica Automotiva: banco inicializado e atualizado com sucesso.")
