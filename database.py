from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text

DATABASE_URL = "postgresql://postgres:@192.168.150.234:5432/new_db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def reset_database():
#     try:
#         db = SessionLocal()
#         # Отключаем внешние ключи
#         db.execute(text("SET session_replication_role = 'replica';"))
#         # Список таблиц для очистки
#         tables = ["daniam02", "new_test1_new_new", "newtest3", "users", "weather", "text05"]
#         for table in tables:
#             db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
#             print(f"✅ Таблица {table} очищена")
#         # Включаем внешние ключи обратно
#         db.execute(text("SET session_replication_role = 'origin';"))
#         db.commit()
#         db.close()

#         print("🎉 База успешно очищена!")

#     except Exception as e:
#         print("❌ Ошибка при сбросе базы:", e)

# # Запуск очистки базы
# reset_database()