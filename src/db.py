import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Projekt-Wurzelverzeichnis ermitteln und lokale .env laden
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_engine() -> Engine:
    """Erstellt eine SQLAlchemy-Engine für die PostgreSQL-Datenbank."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL wurde nicht gefunden. Bitte in der lokalen .env-Datei setzen."
        )
    return create_engine(database_url, pool_pre_ping=True)


def run_sql_file(sql_path: str | Path, engine: Engine | None = None) -> None:
    """Führt eine SQL-Datei (z. B. sql/schema.sql) auf der Datenbank aus."""
    target_engine = engine or get_engine()
    sql_file = Path(sql_path)
    if not sql_file.is_absolute():
        sql_file = BASE_DIR / sql_file

    sql_content = sql_file.read_text(encoding="utf-8")
    with target_engine.begin() as conn:
        conn.execute(text(sql_content))


if __name__ == "__main__":
    eng = get_engine()
    with eng.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
        print("Verbunden mit:", version)
        run_sql_file("sql/schema.sql", engine=eng)
        print("Schema sql/schema.sql erfolgreich ausgeführt.")