from pathlib import Path
import pandas as pd
from sqlalchemy import text
from src.db import get_engine

DATA_RAW = Path("data/raw")

CANTON_TO_LANG = {
    "AG": "German", "AI": "German", "AR": "German", "BL": "German",
    "BS": "German", "GL": "German", "LU": "German", "NW": "German",
    "OW": "German", "SG": "German", "SH": "German", "SO": "German",
    "SZ": "German", "TG": "German", "UR": "German", "ZG": "German",
    "ZH": "German",
    "GE": "French", "JU": "French", "NE": "French", "VD": "French",
    "TI": "Italian",
    # Zweisprachige Kantone bei Bedarf gezielt verfeinern:
    "BE": "German", "FR": "French", "VS": "French", "GR": "German",
}


def detect_sep(csv_path: Path) -> str:
    first_line = csv_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[0]
    return ";" if first_line.count(";") > first_line.count(",") else ","


def _parse_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace("'", "", regex=False)
        .str.replace("\u2019", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def load_communes(communes_file: Path) -> pd.DataFrame:
    df = pd.read_csv(communes_file, sep=detect_sep(communes_file), encoding="utf-8-sig")
    df = df.rename(
        columns={
            "BFS Gde-nummer": "bfs_id",
            "Gemeindename": "municipality_name",
            "Kanton": "canton",
        }
    )
    df["bfs_id"] = _parse_numeric(df["bfs_id"])
    df = df.dropna(subset=["bfs_id", "municipality_name", "canton"]).copy()
    df["bfs_id"] = df["bfs_id"].astype(int)
    df["municipality_name"] = df["municipality_name"].astype(str).str.strip()
    df["canton"] = df["canton"].astype(str).str.strip().str.upper().str[:2]
    df["language_region"] = df["canton"].map(CANTON_TO_LANG).fillna("German")

    return (
        df[["bfs_id", "municipality_name", "canton", "language_region"]]
        .drop_duplicates(subset=["bfs_id"], keep="last")
        .reset_index(drop=True)
    )


def load_population(population_file: Path, period_ref: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(population_file, sep=detect_sep(population_file), encoding="utf-8-sig")
    if "INDICATORS" in df.columns:
        df = df[df["INDICATORS"].astype(str).str.strip() == "Ind_01_01"].copy()
    if period_ref is not None and "PERIOD_REF" in df.columns:
        df = df[df["PERIOD_REF"].astype(str).str.strip() == str(period_ref)].copy()

    df = df.rename(columns={"CODE_REGION": "bfs_id", "VALUE": "population"})
    df["bfs_id"] = _parse_numeric(df["bfs_id"])
    df["population"] = _parse_numeric(df["population"])
    # Filtert u. a. 'CH' und nicht-numerische Aggregate heraus
    df = df.dropna(subset=["bfs_id", "population"]).copy()
    df["bfs_id"] = df["bfs_id"].astype(int)
    df["population"] = df["population"].round().astype(int)

    return (
        df[["bfs_id", "population"]]
        .drop_duplicates(subset=["bfs_id"], keep="last")
        .reset_index(drop=True)
    )


def load_area_km2(area_file: Path) -> pd.DataFrame:
    df = pd.read_csv(area_file, sep=detect_sep(area_file), encoding="utf-8-sig")

    # Im SDMX-Export heisst die Spalte mit dem BFS-Code typischerweise 'REGION', sonst Fallback
    code_col = next(
        (c for c in ["REGION", "CODE_REGION", "BfsCode", "bfs_id"] if c in df.columns),
        None,
    )
    if code_col is None:
        raise ValueError(f"Keine BFS-Code-Spalte in {area_file} gefunden. Spalten: {list(df.columns)}")

    # Wertespalte suchen (z. B. OBS_VALUE / VALUE / Wert; falls nicht benannt, letzte numerische Spalte)
    val_col = next(
        (c for c in ["OBS_VALUE", "VALUE", "Value", "Wert"] if c in df.columns),
        None,
    )
    if val_col is None:
        candidate_cols = [
            c for c in df.columns
            if c not in {"STRUCTURE", "STRUCTURE_ID", "STRUCTURE_NAME", "ACTION", "NOLC", "Bodenbedeckung", "PERIOD", "Erhebungsperiode", "REGION"}
        ]
        # Letzte Spalte im SDMX-CSV ist oft der numerische Wert, wenn die Beschriftung davor steht
        val_col = candidate_cols[-1] if candidate_cols else df.columns[-1]

    df = df.copy()
    # Nur rein numerische Codes behalten (filtert Bezirke wie 'B_1910' oder Kantone wie 'JU' heraus)
    df["bfs_id"] = _parse_numeric(df[code_col])
    df["area_ha"] = _parse_numeric(df[val_col])
    df = df.dropna(subset=["bfs_id", "area_ha"]).copy()
    df["bfs_id"] = df["bfs_id"].astype(int)

    grouped = df.groupby("bfs_id", as_index=False)["area_ha"].sum()
    grouped["area_km2"] = (grouped["area_ha"] / 100.0).round(2)

    return grouped[["bfs_id", "area_km2"]]


def load_municipalities(
    communes_file: Path = DATA_RAW / "gemeindestand.csv",
    population_file: Path = DATA_RAW / "einwohnerzahl.csv",
    area_file: Path = DATA_RAW / "flaechen.csv",
) -> int:
    df_comm = load_communes(communes_file)
    df_pop = load_population(population_file)
    df_area = load_area_km2(area_file)

    merged = (
        df_comm
        .merge(df_pop, on="bfs_id", how="left")
        .merge(df_area, on="bfs_id", how="left")
    )

    records = [
        {
            "bfs_id": int(row["bfs_id"]),
            "municipality_name": row["municipality_name"],
            "canton": row["canton"],
            "language_region": row["language_region"],
            "postal_code": None,
            "population": None if pd.isna(row["population"]) else int(row["population"]),
            "area_km2": None if pd.isna(row["area_km2"]) else float(row["area_km2"]),
            "youth_share_pct": None,
            "median_income_chf": None,
            "tax_strength_index": None,
            "latitude": None,
            "longitude": None,
        }
        for _, row in merged.iterrows()
    ]

    upsert_sql = text(
        """
        INSERT INTO municipalities (
            bfs_id,
            municipality_name,
            canton,
            language_region,
            postal_code,
            population,
            area_km2,
            youth_share_pct,
            median_income_chf,
            tax_strength_index,
            latitude,
            longitude
        )
        VALUES (
            :bfs_id,
            :municipality_name,
            :canton,
            :language_region,
            :postal_code,
            :population,
            :area_km2,
            :youth_share_pct,
            :median_income_chf,
            :tax_strength_index,
            :latitude,
            :longitude
        )
        ON CONFLICT (bfs_id) DO UPDATE SET
            municipality_name = EXCLUDED.municipality_name,
            canton = EXCLUDED.canton,
            language_region = EXCLUDED.language_region,
            postal_code = COALESCE(EXCLUDED.postal_code, municipalities.postal_code),
            population = COALESCE(EXCLUDED.population, municipalities.population),
            area_km2 = COALESCE(EXCLUDED.area_km2, municipalities.area_km2),
            youth_share_pct = COALESCE(EXCLUDED.youth_share_pct, municipalities.youth_share_pct),
            median_income_chf = COALESCE(EXCLUDED.median_income_chf, municipalities.median_income_chf),
            tax_strength_index = COALESCE(EXCLUDED.tax_strength_index, municipalities.tax_strength_index),
            latitude = COALESCE(EXCLUDED.latitude, municipalities.latitude),
            longitude = COALESCE(EXCLUDED.longitude, municipalities.longitude);
        """
    )

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(upsert_sql, records)

    return len(records)


if __name__ == "__main__":
    count = load_municipalities()
    print(f"Upsert abgeschlossen: {count} Gemeinden verarbeitet.")