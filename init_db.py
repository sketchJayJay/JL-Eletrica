import os
from app import app, db

with app.app_context():
    os.makedirs("/app/data", exist_ok=True)
    db.create_all()
    print("JL Elétrica: banco de dados inicializado com sucesso.")
