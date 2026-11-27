import argparse
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Projekt-Wurzelverzeichnis ermitteln und lokale .env laden
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MANAGED_TABLES = ("municipalities", "clubs", "players")


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


def get_table_counts(engine: Engine) -> dict[str, int | None]:
    """Prüft die Existenz der verwalteten Tabellen und gibt deren Zeilenanzahl zurück."""
    counts: dict[str, int | None] = {}
    with engine.connect() as conn:
        for table in MANAGED_TABLES:
            exists = conn.execute(
                text("SELECT to_regclass(:table_name) IS NOT NULL;"),
                {"table_name": f"public.{table}"},
            ).scalar()
            if exists:
                counts[table] = conn.execute(
                    text(f"SELECT COUNT(*) FROM public.{table};")
                ).scalar_one()
            else:
                counts[table] = None
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prüft die PostgreSQL-Verbindung und Tabellenstände (ohne destruktive Aktionen)."
    )
    parser.add_argument(
        "--reset-schema",
        action="store_true",
        help="Führt sql/schema.sql aus (ACHTUNG: löscht bestehende Tabellen und Daten!).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Bestätigt --reset-schema ohne interaktive Eingabeaufforderung.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    eng = get_engine()

    with eng.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
    print("Verbunden mit:", version)

    counts = get_table_counts(eng)
    print("Tabellenstatus:")
    for table, count in counts.items():
        if count is None:
            print(f"  - {table}: nicht vorhanden")
        else:
            print(f"  - {table}: {count} Zeilen")

    if args.reset_schema:
        if not args.yes:
            try:
                confirm = input(
                    "ACHTUNG: Alle Tabellen und Daten werden zurückgesetzt! "
                    "Tippe 'RESET' zum Bestätigen: "
                )
            except (EOFError, KeyboardInterrupt):
                print("\nAbgebrochen. Schema wurde nicht zurückgesetzt.")
                return
            if confirm.strip() != "RESET":
                print("Abgebrochen. Schema wurde nicht zurückgesetzt.")
                return

        run_sql_file("sql/schema.sql", engine=eng)
        print("Schema sql/schema.sql erfolgreich ausgeführt.")


if __name__ == "__main__":
    main()