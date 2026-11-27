import argparse
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import text
from urllib3.util.retry import Retry

from src.db import get_engine

DATA_RAW = Path("data/raw")

SWISSTOPO_AMTOVZ_URL = (
    "https://data.geo.admin.ch/ch.swisstopo-vd.ortschaftenverzeichnis_plz/"
    "ortschaftenverzeichnis_plz/ortschaftenverzeichnis_plz_4326.csv.zip"
)
BFS_REGIONAL_PORTRAITS_URL = (
    "https://dam-api.bfs.admin.ch/hub/api/dam/assets/16484444/master"
)
BFS_STATPOP_PXWEB_URL = (
    "https://www.pxweb.bfs.admin.ch/api/v1/de/"
    "px-x-0102010000_101/px-x-0102010000_101.px"
)
ESTV_DBST_2023_URL = (
    "https://www.estv.admin.ch/dam/de/sd-web/krlJTZvG3JLA/"
    "statistik-dbst-np-gemeinden-2023-500.xlsx"
)

# Nicht-politische Spezialgebiete im Ortschaftenverzeichnis (Staatswald Galm, Comunanza)
NON_MUNICIPALITY_BFS_IDS = {2391, 5391}

CANTON_TO_LANG = {
    "AG": "German", "AI": "German", "AR": "German", "BL": "German",
    "BS": "German", "GL": "German", "LU": "German", "NW": "German",
    "OW": "German", "SG": "German", "SH": "German", "SO": "German",
    "SZ": "German", "TG": "German", "UR": "German", "ZG": "German",
    "ZH": "German",
    "GE": "French", "JU": "French", "NE": "French", "VD": "French",
    "TI": "Italian",
    # Zweisprachige Kantone (Basis-Default, wird über BFS_LANG_OVERRIDES & swisstopo verfeinert):
    "BE": "German", "FR": "French", "VS": "French", "GR": "German",
}

SWISSTOPO_LANG_MAP = {
    "de": "German",
    "fr": "French",
    "it": "Italian",
}

# Explizite Sprachregion-Overrides für zweisprachige/mehrsprachige Kantone (BE, FR, VS, GR)
BFS_LANG_OVERRIDES: dict[int, str] = {
    # BE: Französischsprachiger Berner Jura -> French; Biel/Bienne -> German (Mehrheitssprache)
    **{bfs_id: "French" for bfs_id in range(431, 451)},
    **{bfs_id: "French" for bfs_id in range(681, 718)},
    **{bfs_id: "French" for bfs_id in range(721, 727)},
    371: "German",   # Biel/Bienne (zweisprachig, Mehrheit Deutsch)
    # FR: Sensebezirk & deutschsprachige Seebezirk-Gemeinden -> German; Fribourg/Bulle -> French
    **{bfs_id: "German" for bfs_id in range(2291, 2312)},
    2275: "German",  # Murten/Morat
    2265: "German",  # Kerzers
    2196: "French",  # Fribourg
    2125: "French",  # Bulle
    # VS: Unter-/Mittelwallis -> French; Oberwallis -> German
    6266: "French",  # Sion
    6248: "French",  # Sierre
    6136: "French",  # Martigny
    6153: "French",  # Monthey
    6002: "German",  # Brig-Glis
    6297: "German",  # Visp
    6007: "German",  # Naters
    # GR: Italienischbünden (Bernina, Bregaglia, Moesa) -> Italian; Chur -> German
    3551: "Italian",  # Brusio
    3561: "Italian",  # Poschiavo
    3792: "Italian",  # Bregaglia
    3804: "Italian",  # Buseno
    3805: "Italian",  # Castaneda
    3808: "Italian",  # Rossa
    3810: "Italian",  # Santa Maria in Calanca
    3821: "Italian",  # Lostallo
    3822: "Italian",  # Mesocco
    3823: "Italian",  # Soazza
    3831: "Italian",  # Cama
    3832: "Italian",  # Grono
    3834: "Italian",  # Roveredo (GR)
    3835: "Italian",  # San Vittore
    3837: "Italian",  # Calanca
    3901: "German",   # Chur
}


def resolve_language_region(
    bfs_id: int, canton: str, swisstopo_lang: str | None = None
) -> str:
    """Bestimmt die Sprachregion (`German`, `French`, `Italian`) deterministisch."""
    if bfs_id in BFS_LANG_OVERRIDES:
        return BFS_LANG_OVERRIDES[bfs_id]
    if swisstopo_lang in {"German", "French", "Italian"}:
        return swisstopo_lang
    return CANTON_TO_LANG.get(canton, "German")


def _http_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "zhaw-swiss-football-analytics/1.0"})
    return session


def download_bfs_sources(
    data_dir: Path = DATA_RAW, force: bool = False
) -> dict[str, Path]:
    """Lädt offizielle Schweizer Open-Data-Quellen in `data_dir` herunter (mit lokalem Cache)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "swisstopo": data_dir / "ortschaftenverzeichnis_plz_4326.csv.zip",
        "regional_portraits": data_dir / "bfs_regionalportraets.csv",
        "statpop": data_dir / "bfs_statpop_2025.csv",
        "estv": data_dir / "estv_dbst_2023_500.xlsx",
    }

    session = _http_session()

    simple_downloads = {
        "swisstopo": SWISSTOPO_AMTOVZ_URL,
        "regional_portraits": BFS_REGIONAL_PORTRAITS_URL,
        "estv": ESTV_DBST_2023_URL,
    }
    for key, url in simple_downloads.items():
        target = paths[key]
        if force or not target.exists() or target.stat().st_size == 0:
            print(f"Lade {key} herunter: {url}")
            resp = session.get(url, timeout=60)
            resp.raise_for_status()
            target.write_bytes(resp.content)
        else:
            print(f"Nutze lokalen Cache für {key}: {target}")

    statpop_target = paths["statpop"]
    if force or not statpop_target.exists() or statpop_target.stat().st_size == 0:
        print(f"Lade statpop (2025) herunter: {BFS_STATPOP_PXWEB_URL}")
        meta_resp = session.get(BFS_STATPOP_PXWEB_URL, timeout=30)
        meta_resp.raise_for_status()
        meta = meta_resp.json()
        vars_info = {v["code"]: v for v in meta["variables"]}
        latest_year = vars_info["Jahr"]["values"][-1]
        gem_var = vars_info["Kanton (-) / Bezirk (>>) / Gemeinde (......)"]
        gem_codes = [
            val
            for val, txt in zip(gem_var["values"], gem_var["valueTexts"])
            if txt.startswith("......")
        ]
        query = {
            "query": [
                {"code": "Jahr", "selection": {"filter": "item", "values": [latest_year]}},
                {
                    "code": "Kanton (-) / Bezirk (>>) / Gemeinde (......)",
                    "selection": {"filter": "item", "values": gem_codes},
                },
                {"code": "Bevölkerungstyp", "selection": {"filter": "item", "values": ["1"]}},
                {
                    "code": "Staatsangehörigkeit (Kategorie)",
                    "selection": {"filter": "item", "values": ["-99999"]},
                },
                {"code": "Geschlecht", "selection": {"filter": "item", "values": ["-99999"]}},
                {
                    "code": "Alter",
                    "selection": {
                        "filter": "item",
                        "values": ["-99999"] + [str(i) for i in range(20)],
                    },
                },
            ],
            "response": {"format": "csv"},
        }
        px_resp = session.post(BFS_STATPOP_PXWEB_URL, json=query, timeout=60)
        px_resp.raise_for_status()
        statpop_target.write_bytes(px_resp.content)
    else:
        print(f"Nutze lokalen Cache für statpop: {statpop_target}")

    return paths


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
    df["language_region"] = [
        resolve_language_region(bid, canton)
        for bid, canton in zip(df["bfs_id"], df["canton"])
    ]

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


def load_swisstopo_places(zip_path: Path) -> pd.DataFrame:
    """Parst swisstopo AMTOVZ (WGS84) und aggregiert PLZ sowie Koordinaten je `bfs_id`."""
    with zipfile.ZipFile(zip_path) as zf:
        csv_name = next(name for name in zf.namelist() if name.endswith(".csv"))
        with zf.open(csv_name) as handle:
            df = pd.read_csv(handle, sep=";", encoding="utf-8-sig")

    df = df.copy()
    df["bfs_id"] = _parse_numeric(df["BFS-Nr"])
    df["plz4"] = _parse_numeric(df["PLZ4"])
    df["longitude"] = _parse_numeric(df["E"])
    df["latitude"] = _parse_numeric(df["N"])
    df["canton"] = df["Kantonskürzel"].astype(str).str.strip().str.upper()
    df["municipality_name"] = df["Gemeindename"].astype(str).str.strip()
    df["swisstopo_lang"] = (
        df["Sprache"].astype(str).str.strip().str.lower().map(SWISSTOPO_LANG_MAP)
        if "Sprache" in df.columns
        else None
    )

    # Liechtenstein (Kantonskürzel fehlt) und nicht-politische Spezialgebiete ausschliessen
    df = df[
        df["bfs_id"].notna()
        & df["plz4"].notna()
        & df["canton"].isin(CANTON_TO_LANG.keys())
    ].copy()
    df["bfs_id"] = df["bfs_id"].astype(int)
    df = df[~df["bfs_id"].isin(NON_MUNICIPALITY_BFS_IDS)].copy()
    df["plz4"] = df["plz4"].astype(int)

    def _mode_lang(series: pd.Series) -> str | None:
        valid = series.dropna()
        if valid.empty:
            return None
        return str(valid.mode().iloc[0])

    grouped = (
        df.groupby("bfs_id", as_index=False)
        .agg(
            municipality_name=("municipality_name", "first"),
            canton=("canton", "first"),
            swisstopo_lang=("swisstopo_lang", _mode_lang),
            postal_code_int=("plz4", "min"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
        )
    )
    grouped["language_region"] = [
        resolve_language_region(int(bid), str(canton), lang)
        for bid, canton, lang in zip(
            grouped["bfs_id"], grouped["canton"], grouped["swisstopo_lang"]
        )
    ]
    grouped["postal_code"] = grouped["postal_code_int"].astype(int).astype(str).str.zfill(4)
    grouped["latitude"] = grouped["latitude"].round(6)
    grouped["longitude"] = grouped["longitude"].round(6)

    return grouped[
        [
            "bfs_id",
            "municipality_name",
            "canton",
            "language_region",
            "postal_code",
            "latitude",
            "longitude",
        ]
    ]


def load_regional_portraits(csv_path: Path) -> pd.DataFrame:
    """Liest Bevölkerung (`Ind_01_01`), Fläche (`Ind_04_01`) und Jugendanteil 0-19 (`Ind_01_04`)."""
    df = pd.read_csv(csv_path, sep=detect_sep(csv_path), encoding="utf-8-sig", low_memory=False)
    df = df[df["INDICATORS"].isin(["Ind_01_01", "Ind_01_04", "Ind_04_01"])].copy()
    df["bfs_id"] = _parse_numeric(df["CODE_REGION"])
    df["value"] = _parse_numeric(df["VALUE"])
    df = df.dropna(subset=["bfs_id", "value"]).copy()
    df["bfs_id"] = df["bfs_id"].astype(int)

    pivoted = (
        df.pivot_table(index="bfs_id", columns="INDICATORS", values="value", aggfunc="last")
        .reset_index()
        .rename(
            columns={
                "Ind_01_01": "population",
                "Ind_04_01": "area_km2",
                "Ind_01_04": "youth_share_pct",
            }
        )
    )
    if "population" in pivoted.columns:
        pivoted["population"] = pivoted["population"].round().astype("Int64")
    if "area_km2" in pivoted.columns:
        pivoted["area_km2"] = pivoted["area_km2"].round(2)
    if "youth_share_pct" in pivoted.columns:
        pivoted["youth_share_pct"] = pivoted["youth_share_pct"].round(2)

    return pivoted


def load_statpop_2025(csv_path: Path) -> pd.DataFrame:
    """Liest aktuelle STATPOP-Bevölkerung und 0-19-Jahre-Jugendanteil aus PXWeb-CSV."""
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="cp1252")
    region_col = df.columns[1]
    df = df.copy()
    df["bfs_id"] = pd.to_numeric(
        df[region_col].astype(str).str.extract(r"^\.\.\.\.\.\.(\d+)")[0],
        errors="coerce",
    )
    df = df.dropna(subset=["bfs_id"]).copy()
    df["bfs_id"] = df["bfs_id"].astype(int)

    youth_col_names = {"0 Jahre", "1 Jahr"} | {f"{i} Jahre" for i in range(2, 20)}
    youth_cols = [c for c in df.columns if c in youth_col_names]

    df["population"] = pd.to_numeric(df["Alter - Total"], errors="coerce")
    df["youth_pop"] = df[youth_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    df = df[df["population"].notna() & (df["population"] > 0)].copy()
    df["youth_share_pct"] = (df["youth_pop"] / df["population"] * 100.0).round(2)
    df["population"] = df["population"].round().astype("Int64")

    return (
        df[["bfs_id", "population", "youth_share_pct"]]
        .drop_duplicates(subset=["bfs_id"], keep="last")
        .reset_index(drop=True)
    )


def load_estv_income_tax(xlsx_path: Path, pop_df: pd.DataFrame) -> pd.DataFrame:
    """Berechnet `median_income_chf` und `tax_strength_index` aus ESTV Direkte Bundessteuer (2023).

    - `median_income_chf`: Interpolierter gruppierter Median des reinen Einkommens aus
      Blatt 511 (Steuerpflichtige mit und ohne Belastung, Normalfälle). Falls für eine
      Kleinstgemeinde Einkommensklassen unterhalb des Medians aus Geheimhaltungsgründen (`-`)
      gesperrt sind, wird auf das arithmetische Mittel (`Reines Einkommen Total / Pflichtige`
      aus den Blättern 522 / 521) zurückgegriffen.
    - `tax_strength_index`: `(bundessteuer_ertrag_pro_kopf / ch_mittelwert) * 100`
      (Schweizer Durchschnitt über alle gematchten Gemeinden = 100.0).
    """
    df511 = pd.read_excel(xlsx_path, sheet_name="511", header=2)
    df521 = pd.read_excel(xlsx_path, sheet_name="521", header=2)
    df522 = pd.read_excel(xlsx_path, sheet_name="522", header=2)
    df524 = pd.read_excel(xlsx_path, sheet_name="524", header=2)

    def _clean_estv(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["bfs_id"] = pd.to_numeric(out["Gemeinde ID"], errors="coerce")
        out = out[out["bfs_id"].notna() & (out["bfs_id"] < 10000)].copy()
        out["bfs_id"] = out["bfs_id"].astype(int)
        return out

    def _estv_num(val) -> float:
        if pd.isna(val):
            return np.nan
        txt = str(val).strip().replace("'", "").replace("\u2019", "")
        if txt in {"", "-", "–"}:
            return np.nan
        return pd.to_numeric(txt, errors="coerce")

    m511 = _clean_estv(df511)
    m521 = _clean_estv(df521)
    m522 = _clean_estv(df522)
    m524 = _clean_estv(df524)

    bracket_cols = list(m511.columns[4:14])
    bracket_bounds = [
        (0.0, 0.0),
        (0.0, 30_000.0),
        (30_000.0, 40_000.0),
        (40_000.0, 50_000.0),
        (50_000.0, 75_000.0),
        (75_000.0, 100_000.0),
        (100_000.0, 200_000.0),
        (200_000.0, 500_000.0),
        (500_000.0, 1_000_000.0),
        (1_000_000.0, 2_000_000.0),
    ]

    def _grouped_median(row: pd.Series) -> float:
        total = _estv_num(row["Total / Totale"])
        if pd.isna(total) or total <= 0:
            return np.nan
        target = total / 2.0
        cum = 0.0
        for (low, high), col in zip(bracket_bounds, bracket_cols):
            count = _estv_num(row[col])
            if pd.isna(count):
                return np.nan
            if cum + count >= target:
                if count <= 0 or low == high:
                    return low
                return round(low + ((target - cum) / count) * (high - low), 2)
            cum += count
        return np.nan

    m511["median_reineinkommen"] = m511.apply(_grouped_median, axis=1)
    m521["n_taxpayers"] = m521["Total / Totale"].map(_estv_num)
    m522["total_reineinkommen"] = m522["Total / Totale"].map(_estv_num)
    m524["total_bundessteuer"] = m524["Total / Totale"].map(_estv_num)

    estv = (
        m511[["bfs_id", "median_reineinkommen"]]
        .merge(m521[["bfs_id", "n_taxpayers"]], on="bfs_id", how="outer")
        .merge(m522[["bfs_id", "total_reineinkommen"]], on="bfs_id", how="outer")
        .merge(m524[["bfs_id", "total_bundessteuer"]], on="bfs_id", how="outer")
        .merge(pop_df[["bfs_id", "population"]], on="bfs_id", how="left")
    )

    mean_income = (estv["total_reineinkommen"] / estv["n_taxpayers"]).round(2)
    estv["median_income_chf"] = estv["median_reineinkommen"].fillna(mean_income).round(2)

    valid_tax = estv[
        estv["total_bundessteuer"].notna()
        & estv["population"].notna()
        & (estv["population"] > 0)
    ]
    ch_mean_per_capita = valid_tax["total_bundessteuer"].sum() / valid_tax["population"].sum()
    estv["tax_strength_index"] = np.where(
        estv["total_bundessteuer"].notna() & estv["population"].notna() & (estv["population"] > 0),
        ((estv["total_bundessteuer"] / estv["population"]) / ch_mean_per_capita * 100.0),
        np.nan,
    )
    estv["tax_strength_index"] = estv["tax_strength_index"].round(2)

    return (
        estv[["bfs_id", "median_income_chf", "tax_strength_index"]]
        .drop_duplicates(subset=["bfs_id"], keep="last")
        .reset_index(drop=True)
    )


def load_municipalities(
    communes_file: Path = DATA_RAW / "gemeindestand.csv",
    population_file: Path = DATA_RAW / "einwohnerzahl.csv",
    area_file: Path = DATA_RAW / "flaechen.csv",
    data_dir: Path = DATA_RAW,
    force_download: bool = False,
) -> int:
    sources = download_bfs_sources(data_dir=data_dir, force=force_download)
    df_sw = load_swisstopo_places(sources["swisstopo"])

    if communes_file.exists():
        df_comm = load_communes(communes_file)
        lang_lookup = df_sw.set_index("bfs_id")["language_region"].to_dict()
        df_comm["language_region"] = [
            BFS_LANG_OVERRIDES.get(int(bid), lang_lookup.get(int(bid), lang))
            for bid, lang in zip(df_comm["bfs_id"], df_comm["language_region"])
        ]
    else:
        df_comm = df_sw[["bfs_id", "municipality_name", "canton", "language_region"]].copy()

    df_rp = load_regional_portraits(sources["regional_portraits"])
    df_sp = load_statpop_2025(sources["statpop"])

    # Basis aus Regionalporträts (Bevölkerung, Fläche, Jugendanteil), überschrieben mit STATPOP 2025
    df_demo = df_rp.merge(df_sp, on="bfs_id", how="outer", suffixes=("_rp", "_sp"))
    df_demo["population"] = df_demo["population_sp"].combine_first(df_demo.get("population_rp"))
    df_demo["youth_share_pct"] = df_demo["youth_share_pct_sp"].combine_first(
        df_demo.get("youth_share_pct_rp")
    )
    df_demo = df_demo[["bfs_id", "population", "area_km2", "youth_share_pct"]].copy()

    # Kompatible Fallbacks, falls lokale CSVs vorliegen
    if population_file.exists():
        df_pop_local = load_population(population_file)
        df_demo = df_demo.merge(
            df_pop_local, on="bfs_id", how="left", suffixes=("", "_local")
        )
        df_demo["population"] = df_demo["population"].combine_first(df_demo["population_local"])
        df_demo = df_demo.drop(columns=["population_local"])
    if area_file.exists():
        df_area_local = load_area_km2(area_file)
        df_demo = df_demo.merge(
            df_area_local, on="bfs_id", how="left", suffixes=("", "_local")
        )
        df_demo["area_km2"] = df_demo["area_km2"].combine_first(df_demo["area_km2_local"])
        df_demo = df_demo.drop(columns=["area_km2_local"])

    df_estv = load_estv_income_tax(sources["estv"], df_demo[["bfs_id", "population"]])

    merged = (
        df_comm
        .merge(df_sw[["bfs_id", "postal_code", "latitude", "longitude"]], on="bfs_id", how="left")
        .merge(df_demo, on="bfs_id", how="left")
        .merge(df_estv, on="bfs_id", how="left")
    )

    records = [
        {
            "bfs_id": int(row["bfs_id"]),
            "municipality_name": row["municipality_name"],
            "canton": row["canton"],
            "language_region": row["language_region"],
            "postal_code": None if pd.isna(row["postal_code"]) else str(row["postal_code"]),
            "population": None if pd.isna(row["population"]) else int(row["population"]),
            "area_km2": None if pd.isna(row["area_km2"]) else float(row["area_km2"]),
            "youth_share_pct": (
                None if pd.isna(row["youth_share_pct"]) else float(row["youth_share_pct"])
            ),
            "median_income_chf": (
                None if pd.isna(row["median_income_chf"]) else float(row["median_income_chf"])
            ),
            "tax_strength_index": (
                None if pd.isna(row["tax_strength_index"]) else float(row["tax_strength_index"])
            ),
            "latitude": None if pd.isna(row["latitude"]) else float(row["latitude"]),
            "longitude": None if pd.isna(row["longitude"]) else float(row["longitude"]),
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
    parser = argparse.ArgumentParser(
        description="Lädt BFS-, swisstopo- und ESTV-Gemeindedaten in PostgreSQL."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Lädt Quelldateien neu herunter und überschreibt den lokalen Cache.",
    )
    args = parser.parse_args()
    count = load_municipalities(force_download=args.refresh)
    print(f"Upsert abgeschlossen: {count} Gemeinden verarbeitet.")