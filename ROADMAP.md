# Project Roadmap – Swiss Football League Analytics (ZHAW)

> **Zweck dieses Dokuments:** Zentrale Steuerungs-, Spezifikations- und Statusdatei für Teammitglieder und AI-Agents.  
> **Arbeitsprotokoll für AI-Agents (STRIKT EINHALTEN):**
> 1. **Vor Arbeitsbeginn:** Abschnitt **2 (Status)**, **3 (Bewertungs-Checkliste)** und **4 (Leitplanken)** lesen.
> 2. **Kleinschrittig arbeiten:** Immer nur **ein Teilpaket** (z. B. `1.3` oder `2.2`) pro Durchlauf umsetzen, testen und verifizieren, bevor das nächste begonnen wird.
> 3. **AI-Einsatz protokollieren (Pflicht für Benotung!):** Nach jeder abgeschlossenen Aufgabe kurz in [docs/AI_USAGE.md](./docs/AI_USAGE.md) ergänzen: genutztes Modell/Tool, Aufgabe, was gut funktioniert hat und **was nicht auf Anhieb geklappt hat / manuell korrigiert werden musste**.
> 4. **Status pflegen:** Nach erfolgreichem Test Checkboxen (`[x]`) und die Status-Tabelle in dieser Datei aktualisieren.

---

## 1. Projektziel, Forschungsfragen & Datenarchitektur

### 1.1 Übergeordnetes Ziel & Forschungsfragen
Das Projekt untersucht den Zusammenhang zwischen **regionaler Wirtschaftskraft & Demografie (BFS/ESTV)**, **Kader- und Spielermarktwerten**, **sportlichem Erfolg** und **Nachwuchsförderung (Academy Talent)** in der Schweizer **Super League** und **Challenge League** – bewusst über eine reine Standard-Vorhersage hinaus im Vergleich zwischen **Ligen**, **Sprachregionen** und **Datenquellen**:

- **FF1 (Regionalökonomie & Marktwert):** Inwiefern hängen Bevölkerung, Steuerkraft/Medianeinkommen und Jugendanteil einer Standortgemeinde mit dem Gesamtmarktwert und sportlichen Erfolg (`points`, `league_rank`) eines Profiklubs zusammen?
- **FF2 (Nachwuchsförderung im Ligen- & Regionenvergleich):** Unterscheidet sich der Anteil eigener Nachwuchsspieler (`is_academy_product` / `academy_share_pct`) signifikant zwischen Super League und Challenge League sowie zwischen den Schweizer Sprachregionen (`German`, `French`, `Italian`)?
- **FF3 (Mehrwert der Datenintegration im Modeling):** Verbessert die Integration sozioökonomischer Gemeindedaten die Vorhersage von Spielermarktwerten bzw. Ausbildungsstatus gegenüber rein sportlichen Spielermerkmalen?

### 1.2 Datenbank & Schema
- **Datenbank:** Cloud PostgreSQL (`Neon`, PostgreSQL 18.7, Datenbank `neondb`) – Schema in [sql/schema.sql](./sql/schema.sql)
- **Tabellen & Beziehungen:**
  - `municipalities` (PK: `bfs_id`) – BFS-Gemeindedaten, Demografie, Wirtschaftskraft, PLZ & WGS84-Koordinaten (`latitude`, `longitude`)
  - `clubs` (PK: `club_id`, `UNIQUE(club_name)`, FK: `bfs_id -> municipalities.bfs_id ON DELETE SET NULL`) – Liga, Saison, Stadionort, Punkte/Rang und aggregierte Kaderkennzahlen
  - `players` (PK: `player_id`, FK: `club_id -> clubs.club_id ON DELETE CASCADE`) – Einzelspieler, Alter, Position, Nationalität, Marktwert, `is_academy_product`, Vertragsende
- **Werte-Konventionen (exakt einhalten!):**
  - `municipalities.language_region`: `'German'`, `'French'`, `'Italian'`
  - `clubs.league`: `'Super League'`, `'Challenge League'`
  - `clubs.season`: `'2025/26'` (einheitlich für alle Klubs eines Scraping-Laufs)

---

## 2. Status-Übersicht (Stand: 2026-11-27)

| Komponente | Pfad | Status | Bemerkung |
| :--- | :--- | :--- | :--- |
| Datenbank-Schema | [sql/schema.sql](./sql/schema.sql) | ✅ Abgeschlossen | Tabellen `municipalities`, `clubs`, `players` inkl. Indizes angelegt |
| DB-Verbindung | [src/db.py](./src/db.py) | ✅ Abgeschlossen | Non-destruktiver Verbindungstest mit Tabellen-Counts; Schema-Reset nur noch über `--reset-schema` + Bestätigung |
| Abhängigkeiten | [requirements.txt](./requirements.txt) | ✅ Abgeschlossen | Alle 19 Pakete definiert und Installation in `.venv` (Python 3.14) verifiziert |
| Env-Vorlage | [.env.example](./.env.example) | ✅ Abgeschlossen | `DATABASE_URL`-Platzhalterzeile eingetragen |
| AI-Protokoll | [docs/AI_USAGE.md](./docs/AI_USAGE.md) | ✅ Angelegt (laufend) | Initial-Setup (`main` mit Gemini Argon) & Roadmap-Review dokumentiert |
| BFS-Gemeinde-Loader | [src/load_bfs.py](./src/load_bfs.py) | 🟡 Teilweise fertig | Basis (`bfs_id`, Name, Kanton, Sprache, Einwohner, Fläche) steht; 6 Spalten noch `None` |
| Transfermarkt-Scraper | [src/scrape_tm.py](./src/scrape_tm.py) | ⬜ Offen | Datei existiert, aktuell leer (0 Zeilen) |
| Notebook 1: Integration & EDA | [notebooks/01_integration_eda.ipynb](./notebooks/01_integration_eda.ipynb) | ⬜ Offen | Datei existiert, noch ohne Zellen |
| Notebook 2: Statistik & Clustering | [notebooks/02_statistics_clustering.ipynb](./notebooks/02_statistics_clustering.ipynb) | ⬜ Offen | Datei existiert, noch ohne Zellen |
| Notebook 3: Modeling | [notebooks/03_modeling.ipynb](./notebooks/03_modeling.ipynb) | ⬜ Offen | Datei existiert, noch ohne Zellen |
| Moodle-Export & Präsentation | `data/export/` & Folien | ⬜ Offen | Konzeptpräsentation (ab Woche 10) & Endabgabe (PDF + Video + ZIP) |

---

## 3. Bewertungs-Matrix gemäss [TASK_DESCRIPTION.md](./TASK_DESCRIPTION.md) (Ziel: 22 / 22 Punkte)

Jede Anforderung aus [TASK_DESCRIPTION.md](./TASK_DESCRIPTION.md) ist hier fest einem Arbeitspaket zugeordnet. Agents dürfen keines dieser Elemente weglassen:

| Kategorie | Anforderung aus `TASK_DESCRIPTION.md` | Wo wird das erfüllt? |
| :--- | :--- | :--- |
| **Minimum (9 Pkt.)** | 1. Eigene Datensammlung via Web Scraping / API (kein Kaggle!) | Phase 3 ([src/scrape_tm.py](./src/scrape_tm.py)) |
| **Minimum** | 2. Integration $\ge 2$ Quellen inkl. Doku von Matching Keys, Inkonsistenzen & **Anzahl verlorener/gewonnener Records** | Phase 2 + Phase 4.1 ([notebooks/01_integration_eda.ipynb](./notebooks/01_integration_eda.ipynb), Sektion Join-Bilanz) |
| **Minimum** | 3. Datenbank-Speicherung inkl. SQL-Queries aus Python | [src/db.py](./src/db.py) + SQL-Abfragen in allen 3 Notebooks |
| **Minimum** | 4. Reichhaltige **nicht-grafische UND grafische** EDA | Phase 4.1 ([notebooks/01_integration_eda.ipynb](./notebooks/01_integration_eda.ipynb)) |
| **Minimum** | 5. Modeling (Regression/Klassifikation) **über Standard-Prediction hinaus** (Gruppen-/Regionen-/Quellenvergleich) | Phase 4.3 ([notebooks/03_modeling.ipynb](./notebooks/03_modeling.ipynb)) |
| **Minimum** | 6. Model Evaluation mit passenden Gütemassen (`R²`, `RMSE`, `MAE`, `Accuracy`, `Precision`, `Recall`, `F1`, `ROC-AUC`) | Phase 4.3 ([notebooks/03_modeling.ipynb](./notebooks/03_modeling.ipynb)) |
| **Minimum** | 7. Korrekte inhaltliche Interpretation der Modellergebnisse & Metriken | Phase 4.3 (Markdown-Diskussion je Modell) |
| **Minimum** | 8. Dokumentation des AI-Einsatzes (Tools, Vor-/Nachteile, **wo AI versagt hat**) | Laufend in `docs/AI_USAGE.md` + Folien + Video |
| **Minimum** | 9. Bereitstellung aller Materialien (Daten + Notebooks) auf Moodle | Phase 5.1 (`data/export/*.csv` + ZIP-Paket) |
| **Bonus (+6 Pkt.)** | B1. Kreativität der Umsetzung | Eigenständiges Schweizer Fussball- & Regionalökonomie-Design |
| **Bonus** | B2. **PostgreSQL** statt SQLite inkl. **SQL Joins & SQL Aggregationen** aus Python | Neon PostgreSQL + explizite `JOIN` & `GROUP BY`-SQL-Queries in Phase 4.1 |
| **Bonus** | B3. Integration **UND Visualisierung geografischer Daten** | `latitude`/`longitude` in Phase 2 + **Schweizer Karten-Plot** in Phase 4.1 |
| **Bonus** | B4. **Chi-Quadrat-Test**, **ANOVA** oder **Korrelationsanalyse** (jeder Test **zwingend mit `p-value`**!) | Phase 4.2 ([notebooks/02_statistics_clustering.ipynb](./notebooks/02_statistics_clustering.ipynb) enthält alle drei!) |
| **Bonus** | B5. **k-Means Clustering** zusätzlich zu Regression/Klassifikation | Phase 4.2 ([notebooks/02_statistics_clustering.ipynb](./notebooks/02_statistics_clustering.ipynb)) |
| **Bonus** | B6. Code in **öffentlichem GitHub-Repository** (URL in Präsentation nennen) | Phase 5.2 (Repo-Visibility `public` + Link auf Folien) |
| **Präsentation (+7 Pkt.)** | Video (`Anzahl Studierende × 5 Min.`), PDF-Folien, AI-Reflexion & **Pflicht-Appendix mit Screenshots/Code-Snippets für Punkte** | Phase 5.2 & 5.3 |

---

## 4. Verbindliche Leitplanken für Agents

1. **Secrets & `.env` niemals anfassen oder ausgeben:**
   - `.env` enthält die produktive `DATABASE_URL`. Niemals mit `cat`/`view` in Ausgaben posten, niemals committen, niemals in Notebooks hardcoden.
2. **KEIN unbeabsichtigtes `DROP TABLE` auf der Cloud-DB:**
   - [sql/schema.sql](./sql/schema.sql) enthält `DROP TABLE IF EXISTS players, clubs, municipalities CASCADE;`.
   - `run_sql_file("sql/schema.sql")` **niemals** ausführen, ohne vorher per `SELECT COUNT(*)` zu prüfen, ob Daten in `municipalities`, `clubs` oder `players` liegen, und ohne explizite Rückfrage an den User!
3. **Aufrufkonvention für Python-Skripte:**
   - Alle Skripte unter `src/` verwenden absolute Projekt-Imports (`from src.db import get_engine`), ausser `python src/db.py` wird direkt gemäss Onboarding-PDF aufgerufen.
   - Standardaufruf aus dem Repo-Root: `python -m src.<modul>` (z. B. `python -m src.load_bfs`, `python -m src.scrape_tm`).
   - In Notebooks am Anfang eine Pfad-Zelle einfügen:
     ```python
     import sys
     from pathlib import Path
     ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
     if str(ROOT) not in sys.path:
         sys.path.insert(0, str(ROOT))
     from src.db import get_engine
     ```
4. **Idempotenz bei DB-Schreibzugriffen:**
   - Loader müssen beliebig oft hintereinander ausführbar sein, ohne Duplikate oder Foreign-Key-Fehler zu erzeugen (`ON CONFLICT ... DO UPDATE` bzw. transaktionales `DELETE` + `INSERT` für `players` pro `club_id`).
5. **Domänen-Sonderfälle zwingend behandeln:**
   - **FC Vaduz (Liechtenstein):** Spielt in der Schweizer Challenge League, liegt aber im Ausland → hat **keine** Schweizer `bfs_id`. Muss mit `bfs_id = NULL` gespeichert werden (kein Abbruch!) und in Notebook 01 als dokumentierter Join-Ausschluss bei Gemeindeanalysen ausgewiesen werden.
   - **Abweichende Stadiongemeinden:** Einige Klubs tragen nicht den exakten BFS-Gemeindenamen im Vereinsnamen (z. B. *Servette FC* spielt in *Lancy* / Genf, *BSC Young Boys* in *Bern*, *Grasshopper Club Zürich* in *Zürich*, *Étoile Carouge FC* in *Carouge (GE)*). Dafür eine explizite Mapping-Tabelle im Code pflegen.
   - **Zweisprachige Kantone (`BE`, `FR`, `VS`, `GR`):** Nicht pauschal nach Kanton zuordnen – zumindest alle zweisprachigen/anderssprachigen Gemeinden (insb. *Biel/Bienne*, *Fribourg*, *Sion*, *Sierre*, *Martigny*, *Monthey*, *Murten/Morat*, *Brig-Glis*, *Visp*, *Naters*) exakt zuweisen.
   - **Stichprobengrösse beachten:** Auf Klub-Ebene existieren nur $N = 22$ Klubs (12 Super League + 10 Challenge League; davon 21 mit Schweizer `bfs_id`). Komplexe ML-Modelle (Random Forest etc.) deshalb auf **Spieler-Ebene ($N \approx 550–650$)** trainieren; auf Klub-Ebene nur nicht-parametrische Tests, einfache Korrelationen, Clustering und stark regularisierte/LOOCV-Analysen verwenden.

---

## 5. Konkreter Schritt-für-Schritt-Umsetzungsplan

### Phase 1: DB-Absicherung, Umgebung & Projekt-Hygiene (ZUERST AUSFÜHREN!)

> **Warum zuerst?** Im Onboarding-PDF steht in Schritt 4 der Befehl `python src/db.py` zum Verbindungstest. Aktuell löscht dieser Aufruf über `sql/schema.sql` die gesamte Datenbank! Task `1.1` behebt diese Gefahr sofort.

- [x] **1.1 [src/db.py](./src/db.py) gegen versehentliches Löschen absichern**
  - **Konkrete Umsetzung in [src/db.py](./src/db.py):**
    - `argparse` im `if __name__ == "__main__":`-Block ergänzen mit optionalem Flag `--reset-schema` (`action="store_true"`).
    - **Standardverhalten (`python src/db.py` oder `python -m src.db` OHNE Flag):**
      1. Verbindet mit `get_engine()`.
      2. Gibt `SELECT version();` aus (`"Verbunden mit: ..."` – kompatibel mit Onboarding-PDF!).
      3. Prüft für `municipalities`, `clubs`, `players` per `to_regclass('public.<tabelle>')`, ob die Tabellen existieren, und gibt deren aktuelle Zeilenanzahl (`SELECT COUNT(*)`) aus.
      4. Führt **NICHT** `sql/schema.sql` aus.
    - **Nur mit `python -m src.db --reset-schema`:** Fragt im Terminal aktiv ` tippe 'RESET' zum Bestätigen: ` ab (oder Flag `--yes`) und führt erst dann `run_sql_file("sql/schema.sql")` aus.
- [x] **1.2 [requirements.txt](./requirements.txt) & [.env.example](./.env.example) befüllen**
  - **Inhalt für [.env.example](./.env.example) (exakt 1 Zeile):**
    ```env
    DATABASE_URL=postgresql://<user>:<password>@<neon-host>/neondb?sslmode=require
    ```
  - **Inhalt für [requirements.txt](./requirements.txt):**
    ```text
    python-dotenv>=1.0
    sqlalchemy>=2.0
    psycopg2-binary>=2.9
    psycopg[binary]>=3.1
    pandas>=2.2
    numpy>=1.26
    requests>=2.31
    beautifulsoup4>=4.12
    lxml>=5.0
    scipy>=1.13
    scikit-learn>=1.5
    statsmodels>=0.14
    matplotlib>=3.8
    seaborn>=0.13
    plotly>=5.20
    folium>=0.16
    jupyter>=1.0
    ipykernel>=6.29
    openpyxl>=3.1
    ```
- [x] **1.3 [.gitignore](./.gitignore) um lokale Rohdaten/Caches ergänzen**
  - Am Ende von [.gitignore](./.gitignore) hinzufügen:
    ```gitignore
    # Local raw data & scraping cache (keep exported snapshots in data/export/ if needed)
    data/raw/
    data/cache/
    ```
  - Ordner `data/raw/` lokal anlegen (`mkdir -p data/raw data/export docs`).
- [x] **1.4 AI-Dokumentationsdatei [docs/AI_USAGE.md](./docs/AI_USAGE.md) anlegen**
  - Markdown-Vorlage mit Tabelle (`Datum | Aufgabe/Datei | AI-Tool & Modell | Was gut funktionierte | Fehler/Probleme der AI & manuelle Korrektur`) angelegt und initialen Stand auf `main` (**Gemini Argon**) dokumentiert. Ab sofort wird jede weitere Agent-Session laufend ergänzt.

**Akzeptanztest Phase 1:**
- `python src/db.py` und `python -m src.db` geben DB-Version und Tabellen-Counts aus, **ohne** Tabellen zu droppen.

---

### Phase 2: Gemeindedaten & Geodaten vervollständigen ([src/load_bfs.py](./src/load_bfs.py))

> **Warum Phase 2 vor dem Scraper?** `clubs.bfs_id` referenziert `municipalities(bfs_id)`. Wenn `municipalities` inklusive `postal_code`, Koordinaten und Sprachregionen zuerst vollständig geladen ist, kann der Scraper in Phase 3 jeden Klub direkt validiert zuordnen.

Aktuell setzt [src/load_bfs.py](./src/load_bfs.py) folgende 6 Spalten auf `None`:
`postal_code`, `youth_share_pct`, `median_income_chf`, `tax_strength_index`, `latitude`, `longitude`.

- [x] **2.1 Offizielle Schweizer Open-Data-Quellen automatisch laden oder in `data/raw/` ablegen**
  - Bevorzugt: Einen reproduzierbaren Download-Helper `download_bfs_sources()` (oder direktes Laden per URL mit lokalem Fallback in `data/raw/`) implementieren, damit kein Teammitglied Dateien manuell zusammensuchen muss:
    1. **PLZ & Geokoordinaten (`postal_code`, `latitude`, `longitude`):**
       - Quelle: **swisstopo – Amtliches Ortschaftenverzeichnis (`AMTOVZ_CSV_WGS84.csv` / `AMTOVZ_CSV_LV95.csv`)** via `data.geo.admin.ch` (`https://data.geo.admin.ch/ch.swisstopo.amtliches-ortschaftenverzeichnis/amtliches-ortschaftenverzeichnis_ch/amtliches-ortschaftenverzeichnis_ch_2056.csv.zip`).
       - Enthält pro Ortschaft: `BFS-Nr`, `PLZ4`, `Gemeindename`, `Kantonskürzel`, `E` / `N` (LV95 → falls LV95, mit Standardformel nach WGS84 `latitude`/`longitude` umrechnen oder WGS84-Spalten nutzen).
       - Aggregation auf `bfs_id` (da eine Gemeinde mehrere PLZ haben kann): kleinste Haupt-PLZ (`MIN(PLZ4)`) als `postal_code` und Mittelwert der Koordinaten (`AVG(lat)`, `AVG(lon)`) pro `bfs_id`.
       - *Zusatzvorteil:* Dieses File liefert auch den offiziellen Gemeindestand (`bfs_id`, `municipality_name`, `canton`), falls `gemeindestand.csv` lokal fehlt!
    2. **Bevölkerung, Fläche & Jugendanteil (`population`, `area_km2`, `youth_share_pct`):**
       - Quelle: **BFS Regionalporträts der Gemeinden (Kennzahlen aller Gemeinden)** via `opendata.swiss` / BFS DAM-API (Excel/CSV „Regionalporträts: Kennzahlen aller Gemeinden“).
       - Enthält in **einer einzigen offiziellen BFS-Tabelle** pro `bfs_id`:
         - Einwohner (`population`)
         - Gesamtfläche in $\text{km}^2$ (`area_km2`)
         - Altersgruppe **0–19 Jahre in %** → direkt als `youth_share_pct` (Wertebereich `0.00` bis `100.00`) übernehmen!
       - Bestehende CSV-Parser (`load_communes`, `load_population`, `load_area_km2`) als kompatiblen Fallback beibehalten.
    3. **Wirtschaftskraft & Einkommen (`median_income_chf`, `tax_strength_index`):**
       - Quelle: **ESTV Direkte Bundessteuer – Natürliche Personen auf Gemeindeebene** (`opendata.swiss` / `estv.admin.ch`, Excel/CSV „Steuerbares Einkommen / Reineinkommen pro Gemeinde“).
       - `median_income_chf`: Median (oder Mittelwert, falls Median für Kleinstgemeinden gesperrt ist – im Code klar dokumentieren!) des Reineinkommens / steuerbaren Einkommens der steuerpflichtigen natürlichen Personen in CHF.
       - `tax_strength_index`: Bundessteuer-Kopfquote pro Einwohner relativ zum Schweizer Mittel $\times 100$ (Schweizer Durchschnitt $= 100.0$), berechnet als `(bundessteuer_ertrag_pro_kopf / ch_mittelwert) * 100`. So hat jede Gemeinde einen konsistenten, schweizweit vergleichbaren Index!
- [ ] **2.2 Sprachregionen für zweisprachige Kantone (`BE`, `FR`, `VS`, `GR`) präzisieren**
  - In [src/load_bfs.py](./src/load_bfs.py) ein explizites Dictionary `BFS_LANG_OVERRIDES: dict[int, str]` (bzw. BFS-Sprachgebiete-CSV) einbauen, das nach dem Kantons-Default greift:
    - Kanton **VS** (Default im Oberwallis `'German'`, Unter-/Mittelwallis `'French'`): Sicherstellen, dass u. a. `6266` (*Sion*), `6248` (*Sierre*), `6136` (*Martigny*), `6153` (*Monthey*) `'French'` erhalten, während *Brig-Glis* (`6002`), *Visp* (`6297`), *Naters* (`6007`) `'German'` erhalten.
    - Kanton **BE**: Französischsprachiger Berner Jura (`bfs_id` 431–449, 681–716, 721–726) → `'French'`; *Biel/Bienne* (`371`) → `'German'` (Mehrheitssprache Deutsch, Zweisprachigkeit in EDA erwähnen).
    - Kanton **FR**: Sensebezirk (`bfs_id` 2291–2311) & Seebezirk-Deutschgemeinden (*Murten/Morat* `2275`, *Kerzers* `2265`) → `'German'`; *Fribourg* (`2196`) & *Bulle* (`2125`) → `'French'`.
    - Kanton **GR**: Italienischbünden (Bezirke Bernina/Moesa/Bregaglia) → `'Italian'`; *Chur* (`3901`) → `'German'`.
- [ ] **2.3 Modularen Upsert & Validierungs-Report in [src/load_bfs.py](./src/load_bfs.py) fertigstellen**
  - Am Ende von `load_municipalities()` eine Kontrollabfrage ausführen und ausgeben:
    - Gesamtzahl Gemeinden in `municipalities` (erwartet: ~2'100+ Schweizer Gemeinden).
    - Anzahl Nicht-`NULL`-Werte je Spalte (`postal_code`, `population`, `area_km2`, `youth_share_pct`, `median_income_chf`, `tax_strength_index`, `latitude`, `longitude`).

**Akzeptanztest Phase 2:**
- `python -m src.load_bfs` läuft fehlerfrei durch und ist idempotent (zweiter Lauf ändert keine Zeilenanzahl).
- Für alle Schweizer Städte mit Super-/Challenge-League-Klubs sind **alle 12 Spalten** in `municipalities` vollständig (`NOT NULL`) befüllt.

---

### Phase 3: Transfermarkt-Scraper & BFS-Mapping ([src/scrape_tm.py](./src/scrape_tm.py))

Ziel: Vollständiges, höfliches und reproduzierbares Web-Scraping für **Super League** (`C1`) und **Challenge League** (`CH2`) für die Saison `2025/26` (bzw. per Konstante `TARGET_SEASON_ID = "2025"` / `SEASON_LABEL = "2025/26"` konfigurierbar).

- [ ] **3.1 Robuster HTTP-Client mit lokalem HTML-Cache**
  - `requests.Session` mit realistischem Desktop-Header (`User-Agent`, `Accept-Language: de-CH,de;q=0.9`), `timeout=20`, `urllib3.util.retry.Retry` (3 Retries mit Backoff bei `429, 500, 502, 503, 504`).
  - Lokaler Dateicache in `data/raw/tm_cache/<hash_or_slug>.html`:
    - Wenn Cache-Datei existiert und `--refresh` nicht gesetzt ist → aus lokalem Cache lesen (schont Transfermarkt-Server und beschleunigt Debugging massiv!).
    - Bei echtem Netzwerk-Request zwingend `time.sleep(random.uniform(2.5, 4.5))` einhalten.
- [ ] **3.2 Liga-Übersicht & aktuelle Tabelle parsen (`clubs`)**
  - **URLs je Liga (`saison_id=2025`):**
    - Super League Startseite: `https://www.transfermarkt.ch/super-league/startseite/wettbewerb/C1/plus/?saison_id=2025`
    - Super League Tabelle: `https://www.transfermarkt.ch/super-league/tabelle/wettbewerb/C1/saison_id/2025`
    - Challenge League Startseite: `https://www.transfermarkt.ch/challenge-league/startseite/wettbewerb/CH2/plus/?saison_id=2025`
    - Challenge League Tabelle: `https://www.transfermarkt.ch/challenge-league/tabelle/wettbewerb/CH2/saison_id/2025`
  - **Extrahierte Felder pro Klub:**
    - `club_name` (kanonischer Vereinsname + Transfermarkt-`verein_id`)
    - `league` (`'Super League'` oder `'Challenge League'`)
    - `season` (`'2025/26'`)
    - `league_rank` (`INTEGER`) und `points` (`INTEGER`) aus der Tabellen-Seite.
- [ ] **3.3 Detail-Kader & Ausbildungsstatus parsen (`players`)**
  - **Kader-Detail-URL pro Klub:**
    `https://www.transfermarkt.ch/<slug>/kader/verein/<verein_id>/saison_id/2025/plus/1`
    *(Wichtig: `/plus/1` liefert die erweiterte Tabelle inklusive Geburtsdatum/Alter, Nationalität, aktuellem Verein/Vorverein, Vertragsende und Marktwert!)*
  - **Zusätzlich für `is_academy_product`:**
    Transfermarkt bietet pro Liga/Klub die Eigengewächs-/Local-Player-Ansicht bzw. im Kader (`/plus/1`) und auf der Vereinsseite „Jugendvereine / Eigene Jugend“ (`/eigengewaechse/verein/<verein_id>`):
    - **Primärquelle (1 Request pro Klub!):** `https://www.transfermarkt.ch/<slug>/eigengewaechse/verein/<verein_id>` – listet exakt alle aktuellen Kaderspieler auf, die aus der **eigenen Jugendabteilung** des Klubs stammen!
    - **Fallback**, falls die Seite leer/anders strukturiert ist: Prüfung des Vorvereins in `/plus/1` auf Vereins-Präfix + `U16`/`U17`/`U18`/`U19`/`U21`/`II`/`Jugend`.
    - Diese Definition im Docstring von `scrape_tm.py` und in Notebook 01 klar dokumentieren.
  - **Parser-Hilfsfunktionen (mit Unit-Selbsttest / Edge-Cases):**
    - `parse_market_value_eur(raw: str) -> float | None`:
      - `"1,50 Mio. €"` / `"1.50 Mio. €"` → `1500000.0`
      - `"450 Tsd. €"` → `450000.0`
      - `"-"`, `""`, `"?"` → `None`
    - `parse_contract_date(raw: str) -> str | None`:
      - `"30.06.2027"` → `"2027-06-30"` (`YYYY-MM-DD`), `"-"` → `None`
    - `normalize_position(raw: str) -> str`:
      - Detailposition oder Hauptkategorie konsistent speichern (z. B. Detailposition behalten wie `'Innenverteidiger'`, `'Zentrales Mittelfeld'`, `'Mittelstürmer'` und in EDA zusätzlich in `'Torwart'`, `'Abwehr'`, `'Mittelfeld'`, `'Sturm'` gruppieren).
    - `nationality`: Erste Flagge (`img.flaggenrahmen['title']`) als Hauptnationalität extrahieren.
  - **Klub-Aggregate direkt aus der geparsten Spielerliste berechnen (Konsistenzgarantie!):**
    - `total_market_value_eur = round(sum(mv for mv in market_values if mv is not None), 2)`
    - `academy_share_pct = round(100.0 * sum(is_academy) / len(players), 2)`
    - `avg_age = round(mean(ages), 2)`
- [ ] **3.4 Stadionort & deterministisches BFS-Mapping (`bfs_id`)**
  - Stadion-Anschrift/PLZ/Ort von der Vereins-Stadionseite (`/<slug>/stadion/verein/<verein_id>`) oder über ein gepflegtes, verifiziertes Override-Mapping auflösen.
  - **Pflicht-Mapping `CLUB_BFS_OVERRIDES` für bekannte Spezialfälle in `src/scrape_tm.py` hinterlegen:**
    - `'FC Vaduz'`: `{"stadium_city": "Vaduz", "postal_code": "9490", "bfs_id": None}` *(Liechtenstein → bewusst `NULL`!)*
    - `'Servette FC'`: `{"stadium_city": "Lancy", "postal_code": "1212", "bfs_id": 6628}` *(Stade de Genève steht in der Gemeinde Lancy, Kanton GE)*
    - `'Étoile Carouge FC'`: `{"stadium_city": "Carouge", "postal_code": "1227", "bfs_id": 6608}`
    - `'BSC Young Boys'`: `{"stadium_city": "Bern", "postal_code": "3014", "bfs_id": 351}`
    - `'Grasshopper Club Zürich'` & `'FC Zürich'`: `{"stadium_city": "Zürich", "postal_code": "8048", "bfs_id": 261}`
    - `'FC Lausanne-Sport'` & `'FC Stade-Lausanne-Ouchy'`: `{"stadium_city": "Lausanne", "postal_code": "1018", "bfs_id": 5586}`
    - `'Yverdon Sport FC'`: `{"stadium_city": "Yverdon-les-Bains", "postal_code": "1400", "bfs_id": 5938}`
    - `'Neuchâtel Xamax FCS'`: `{"stadium_city": "Neuchâtel", "postal_code": "2000", "bfs_id": 6458}`
    - `'FC Stade Nyonnais'`: `{"stadium_city": "Nyon", "postal_code": "1260", "bfs_id": 5724}`
    - `'FC Rapperswil-Jona'`: `{"stadium_city": "Rapperswil-Jona", "postal_code": "8640", "bfs_id": 3340}`
    - Alle übrigen Schweizer Klubs über exakten Match auf `municipalities.municipality_name` / `postal_code` auflösen und vor dem DB-Insert prüfen, dass die gefundene `bfs_id` tatsächlich in `municipalities` existiert!
- [ ] **3.5 Idempotenter Datenbank-Upsert**
  - Innerhalb einer Transaktion (`with engine.begin() as conn:`):
    1. `INSERT INTO clubs (...) VALUES (...) ON CONFLICT (club_name) DO UPDATE SET ... RETURNING club_id;`
    2. `DELETE FROM players WHERE club_id = :club_id;`
    3. `INSERT INTO players (...) VALUES (...);` für alle Kaderspieler dieses Klubs.
  - Am Ende Zusammenfassung loggen: Anzahl Klubs je Liga, Anzahl Spieler gesamt, Anzahl Klubs mit `bfs_id IS NULL` (erwartet: genau 1, falls FC Vaduz in der Challenge League spielt).

**Akzeptanztest Phase 3:**
- `python -m src.scrape_tm` läuft fehlerfrei durch; 22 Klubs (12 SL + 10 CL) und ~550–650 Spieler in PostgreSQL.
- Ein direkter Zweitlauf aus dem Cache (`python -m src.scrape_tm`) dauert wenige Sekunden und verändert die Zeilenanzahl in `clubs` und `players` um `0`.

---

### Phase 4: Analyse-, Statistik- & Modeling-Notebooks ([notebooks/](./notebooks))

> **Wichtige Regeln für alle 3 Notebooks:**
> - Alle Daten werden live per SQL über `get_engine()` aus der Neon-PostgreSQL-Datenbank abgefragt.
> - Jedes Notebook beginnt mit einer kurzen Markdown-Einleitung (Ziel & Bezug zu den Forschungsfragen FF1–FF3) und endet mit einem strukturierten **Fazit**.
> - Alle Achsen sind beschriftet (inkl. Einheiten wie `EUR`, `CHF`, `%`), Titel sind aussagekräftig, Farbschemata einheitlich.

#### 4.1 [notebooks/01_integration_eda.ipynb](./notebooks/01_integration_eda.ipynb) – SQL-Integration, Datenqualität, EDA & Geokarte
- [ ] **Block A – SQL Joins & SQL Aggregationen (Bonus-Kriterium B2!):**
  - Mindestens **zwei echte SQL-Abfragen mit `JOIN` und `GROUP BY` direkt in PostgreSQL** ausführen und deren SQL-Code sichtbar in Zellen zeigen:
    1. Klub-Gemeinde-Join (`SELECT c.*, m.municipality_name, m.canton, m.language_region, m.population, m.area_km2, m.youth_share_pct, m.median_income_chf, m.tax_strength_index, m.latitude, m.longitude FROM clubs c LEFT JOIN municipalities m ON c.bfs_id = m.bfs_id`).
    2. Aggregierte SQL-Auswertung über alle 3 Tabellen (`JOIN clubs`, `JOIN municipalities`, `GROUP BY c.league, m.language_region` mit `COUNT(p.player_id)`, `AVG(p.market_value_eur)`, `SUM(CASE WHEN p.is_academy_product THEN 1 ELSE 0 END)`).
- [ ] **Block B – Dokumentation der Datenintegration & Join-Verlustbilanz (Pflichtkriterium Minimum 2!):**
  - Übersichtstabelle ausgeben und im Markdown kommentieren:
    - Anzahl Gemeinden in `municipalities` vs. gematchte Fussball-Gemeinden.
    - Anzahl Klubs vor Join (`22`), nach `INNER JOIN` (`21`), verlorene Klubs bei `INNER JOIN` (`1`: **FC Vaduz**, Liechtenstein – Begründung dokumentieren!).
    - Dokumentierte Namens-/Standort-Inkonsistenzen und wie sie gelöst wurden (z. B. *Servette FC → Lancy*, zweisprachige Gemeinden wie *Biel/Bienne*, *Sion*, *Fribourg*).
    - Missing-Values-Report pro Spalte in `clubs`, `players` und gematchten `municipalities`.
- [ ] **Block C – Feature Engineering (in Pandas für Folgeanalysen):**
  - `log_market_value = np.log1p(market_value_eur)`
  - `pop_density = population / area_km2`
  - `market_value_per_capita = total_market_value_eur / population`
  - `position_group` (`Torwart`, `Abwehr`, `Mittelfeld`, `Sturm`)
  - `contract_remaining_months` (Differenz `contract_until` zum Stichtag der Saison)
- [ ] **Block D – Nicht-grafische EDA (Pflichtkriterium Minimum 4!):**
  - Deskriptive Statistik-Tabellen (`count`, `mean`, `std`, `min`, `25%`, `50%`, `75%`, `max`, `skewness`) für Spieler- und Klub-Ebene.
  - Gruppierte Kennzahlentabellen nach `league` (`Super League` vs. `Challenge League`) und nach `language_region` (`German`, `French`, `Italian`).
  - Kontingenz-/Kreuztabelle (`pd.crosstab` mit Zeilen-%): `position_group` $\times$ `is_academy_product` sowie `league` $\times$ `language_region`.
- [ ] **Block E – Grafische EDA (Pflichtkriterium Minimum 4!):**
  1. Verteilung der Spielermarktwerte: Rohskala vs. `log10`/`log1p`-Skala (Histogramm + KDE) – begründet die Log-Transformation fürs Modeling!
  2. Boxplot/Violinplot: `academy_share_pct` und `market_value_eur` nach `league` und `language_region`.
  3. Regressions-Scatterplot: `tax_strength_index` (bzw. `median_income_chf` / `log(population)`) vs. `log(total_market_value_eur)` und `points`, beschriftet mit Klubnamen.
  4. Alter vs. Marktwert-Kurve (`age` vs. `log_market_value`, getrennt nach `is_academy_product`).
  5. Korrelations-Heatmap (Spearman) aller numerischen Klub- und Gemeindevariablen.
- [ ] **Block F – Geografische Karten-Visualisierung (Bonus-Kriterium B3!):**
  - Schweizer Karte mit `plotly.express.scatter_map` (OpenStreetMap-Stil, kein API-Key nötig!) oder `folium`:
    - Koordinaten aus `municipalities.latitude` / `longitude` (optional FC Vaduz separat markiert).
    - Punktgrösse = `total_market_value_eur`, Punktfarbe = `league` (oder `academy_share_pct`), Hover-Infos = Klubname, Gemeinde, Einwohner, Steuerkraft/Medianeinkommen, Academy-Anteil.
    - Zusätzlich statischen Fallback-Plot (`matplotlib` mit Schweizer Koordinatennetz / Kantonskürzeln) rendern, damit die Karte auch im statischen PDF/GitHub-Preview sichtbar bleibt!

#### 4.2 [notebooks/02_statistics_clustering.ipynb](./notebooks/02_statistics_clustering.ipynb) – Hypothesentests & k-Means Clustering
- [ ] **Block A – Methodisches Setup & Normalverteilungsprüfung:**
  - Signifikanzniveau $\alpha = 0.05$ festlegen; Shapiro-Wilk-Test (`scipy.stats.shapiro`) auf Schlüsselvariablen durchführen, um parametrische vs. nicht-parametrische Tests sauber zu begründen.
- [ ] **Block B – Statistische Tests (Bonus-Kriterium B4 – JEDER Test zwingend mit Teststatistik & exaktem `p-value`!):**
  1. **Chi-Quadrat-Unabhängigkeitstest (`scipy.stats.chi2_contingency`):**
     - *Test 1a:* Hängt `is_academy_product` (`True`/`False`) von der Liga (`Super League` vs. `Challenge League`) ab? ($H_0$, $H_1$, Kontingenztabelle, erwartete Häufigkeiten $\ge 5$ prüfen, $\chi^2$, `df`, **`p-value`**, Cramérs $V$).
     - *Test 1b:* Hängt `is_academy_product` von der `language_region` (`German`, `French`, `Italian`) ab? ($\chi^2$, `df`, **`p-value`**).
  2. **Einfaktorielle ANOVA (`scipy.stats.f_oneway`) + Kruskal-Wallis-Check (`scipy.stats.kruskal`):**
     - Unterscheidet sich der mittlere logarithmierte Spielermarktwert `log(market_value_eur)` (oder das Spieleralter `age`) signifikant zwischen den drei Sprachregionen (`German`, `French`, `Italian`) bzw. zwischen den 4 Positionsgruppen? ($F$-Wert, **`p-value`**, Levene-Test auf Varianzhomogenität, ggf. Tukey-HSD Post-hoc-Test).
  3. **Korrelationsanalyse (`scipy.stats.pearsonr` & `scipy.stats.spearmanr`):**
     - Paarweise Tests mit **Korrelationskoeffizient $r$ / $\rho$ UND `p-value`** auf Klub-Ebene ($n = 21$ Schweizer Klubs):
       - `population` vs. `total_market_value_eur`
       - `median_income_chf` / `tax_strength_index` vs. `total_market_value_eur`
       - `youth_share_pct` vs. `academy_share_pct`
       - `total_market_value_eur` vs. `points` (sportlicher Erfolg)
  4. **Zwei-Gruppen-Vergleich (`scipy.stats.mannwhitneyu` & `ttest_ind`):**
     - `academy_share_pct` und `avg_age` zwischen Super League und Challenge League (inkl. `p-value`).
  - Alle Testergebnisse am Ende in einer übersichtlichen **Summary-Tabelle** (`Hypothese | Test | Statistik | p-Wert | H0 verworfen? | Inhaltliche Deutung`) zusammenfassen!
- [ ] **Block C – k-Means Clustering auf Klub-Ebene (Bonus-Kriterium B5!):**
  - Datensatz: Alle Klubs mit vollständigen Gemeindedaten ($n = 21$; Umgang mit FC Vaduz explizit erklären).
  - Features (standardisiert mit `StandardScaler`): z. B. `log(total_market_value_eur)`, `academy_share_pct`, `avg_age`, `log(population)`, `median_income_chf` (bzw. `tax_strength_index`), `youth_share_pct`.
  - Optimale Clusterzahl $k \in \{2, 3, 4, 5, 6\}$ mittels **Elbow-Methode (Inertia)** und **Silhouette-Score** bestimmen und grafisch nebeneinander plotten.
  - `KMeans(n_clusters=k_opt, random_state=42, n_init=20)` fitten.
  - **Visualisierung & Interpretation:**
    - 2D-PCA-Biplot (PC1 vs. PC2 inkl. erklärter Varianz in %, Klubnamen als Textlabels, Clusterfarben und Zentroide).
    - Tabelle der Cluster-Mittelwerte in Originalskala + sprechende Cluster-Namen (z. B. *Cluster 1: Finanzstarke Grossstadt-Spitzenklubs*, *Cluster 2: Regionale Ausbildungs-Klubs*, etc.).

#### 4.3 [notebooks/03_modeling.ipynb](./notebooks/03_modeling.ipynb) – Regression & Klassifikation (mit Quellen- & Gruppenvergleich)
- [ ] **Block A – Forschungsdesign jenseits von Standard-Prediction (Pflichtkriterium Minimum 5!):**
  - Expliziter Modellvergleich **ohne vs. mit BFS-Gemeindedaten** (Ablationsstudie zu FF3) sowie Vergleich der Modellgüte/Residuen zwischen **Super League vs. Challenge League** und **Sprachregionen**.
- [ ] **Block B – Teil 1: Regression – Spielermarktwert vorhersagen (`log1p(market_value_eur)`)**
  - Zielvariable: `y = np.log1p(market_value_eur)` (nur Spieler mit bekanntem Marktwert, $n \approx 550+$).
  - Preprocessing über `sklearn.compose.ColumnTransformer` + `Pipeline` (`StandardScaler` für Numerik, `OneHotEncoder(drop='first', handle_unknown='ignore')` für Kategorik, `SimpleImputer` innerhalb der Pipeline – kein Data Leakage!).
  - **Drei Feature-Sets & Modellfamilien systematisch vergleichen (80/20 Train-Test-Split `random_state=42` + 5-Fold Cross-Validation):**
    1. *Baseline:* `DummyRegressor(strategy="mean")`
    2. *Basis-Modell (nur Sport/Transfermarkt):* `age`, `age_squared`, `position_group`, `is_academy_product`, `contract_remaining_months`, `league`, `swiss_nationality` → `Ridge` & `RandomForestRegressor`
    3. *Integriertes Modell (Sport + BFS-Gemeinde):* Basis-Features + `log_population`, `pop_density`, `youth_share_pct`, `median_income_chf`, `tax_strength_index`, `language_region` → `Ridge`, `Lasso` & `RandomForestRegressor` (bzw. `HistGradientBoostingRegressor`).
  - **Zusätzlicher Robustheitscheck:** `GroupKFold(groups=club_id)` berechnen und diskutieren, wie stark Klub-Zugehörigkeit die Generalisierung auf ungesehene Klubs beeinflusst.
  - **Pflicht-Metriken & Plots (Minimum 6 & 7):**
    - Vergleichstabelle mit **`R²`**, **`RMSE`**, **`MAE`** (auf Log-Skala sowie rücktransformiert in EUR).
    - Predicted-vs.-Actual-Plot, Residuenplot und Gruppen-Auswertung der Residuen nach `language_region` und `league` (welche Klubs/Regionen über- oder unterperformen ihren erwarteten Marktwert?).
    - Feature-Importance- / Koeffizienten-Plot mit klarer fachlicher Interpretation.
- [ ] **Block C – Teil 2: Klassifikation – Nachwuchsstatus (`is_academy_product`) vorhersagen**
  - Zielvariable: `is_academy_product` (`0`/`1`) auf Spieler-Ebene (Klassenverteilung zuerst ausgeben!).
  - Modelle: `DummyClassifier(strategy="most_frequent")`, `LogisticRegression(class_weight="balanced", max_iter=1000)` und `RandomForestClassifier(class_weight="balanced", random_state=42)` mit `StratifiedKFold(n_splits=5)`.
  - Wieder Vergleich *nur Spieler/Klub-Features* vs. *inkl. regionale Demografie (`youth_share_pct`, `population`, `language_region`, `median_income_chf`)*.
  - **Pflicht-Metriken & Plots (Minimum 6 & 7):**
    - **`Accuracy`**, **`Precision`**, **`Recall`**, **`F1-Score`**, **`ROC-AUC`**.
    - Confusion Matrix (`ConfusionMatrixDisplay`), ROC-Kurve (`RocCurveDisplay`) und Interpretation der Odds Ratios (`exp(coef_)` der logistischen Regression).
- [ ] **Block D – Gesamtfazit & Limitationen:**
  - Beantwortung von FF1–FF3, Diskussion von Querschnittsdaten (1 Saison), kleiner Klubanzahl ($n = 22$), Pendlereinzugsgebieten rund um Grossstädte und möglichen Erweiterungen (Mehr-Saison-Panel).

**Akzeptanztest Phase 4:**
- Alle 3 Notebooks laufen mit `jupyter nbconvert --to notebook --execute --inplace notebooks/01_integration_eda.ipynb` (analog `02` und `03`) von oben nach unten **ohne jede Fehlermeldung** durch und speichern alle generierten Plots direkt im Notebook.

---

### Phase 5: Reproduzierbarer Moodle-Export, Präsentationen & Abgabe

- [ ] **5.1 Daten-Snapshot für Moodle-Abgabe exportieren (`data/export/`)**
  - Kleines Export-Skript oder Zelle erstellen, das den finalen Stand von `municipalities`, `clubs` und `players` als UTF-8-CSVs nach `data/export/` schreibt (`municipalities.csv`, `clubs.csv`, `players.csv`).
  - Grund: Gemäss [TASK_DESCRIPTION.md](./TASK_DESCRIPTION.md) muss `materials_group_XX.zip` **alle Daten und Notebooks** enthalten, damit Dozierende die Abgabe auch unabhängig von der Cloud-DB prüfen können.
- [ ] **5.2 Konzeptpräsentation (ab Woche 10 vor Ort in Winterthur, 10 Min.)**
  - PDF-Foliensatz gemäss den 8 Bewertungskriterien aus [TASK_DESCRIPTION.md](./TASK_DESCRIPTION.md) erstellen:
    1. Titel, Gliederung & **vollständige Namen aller Gruppenmitglieder**
    2. Hintergrund & Problemstellung
    3. Ziel & klar formulierte Forschungsfragen (FF1–FF3)
    4. Datenquellen (`transfermarkt.ch`, BFS/ESTV/swisstopo) & 3-Tabellen-Schema (`municipalities`, `clubs`, `players`)
    5. Methoden (SQL-Integration, EDA + Geokarte, $\chi^2$/ANOVA/Korrelation, k-Means, Regression & Klassifikation)
    6. Erwartete Resultate (rückgebunden an FF1–FF3)
- [ ] **5.3 Öffentliches GitHub-Repository & [README.md](./README.md) finalisieren (Bonus B6!)**
  - Sicherstellen, dass `github.com/steinjo6/zhaw-data-analytics-swiss-football` auf **`Public`** steht (vorher per `git log -p` prüfen, dass niemals Credentials committed wurden!).
  - [README.md](./README.md) mit Projektbeschreibung, Architekturdiagramm, Setup-Anleitung und Reproduktionsbefehlen ausbauen.
- [ ] **5.4 Finale Moodle-Abgabe zusammenstellen (ein Gruppenmitglied reicht mit Gruppennummer ein)**
  1. `presentation_group_XX.pdf`:
     - Pflichtstruktur: Titel + alle Studierendennamen → Introduction → Materials & Methods → Results & Discussion → Conclusions → **Reflection on AI usage** ( aus `docs/AI_USAGE.md`).
     - **WICHTIG – Pflicht-Appendix am Ende der PDF (`IMPORTANT!!!` in `TASK_DESCRIPTION.md`):** Tabellarische Auflistung aller 9 Mindestpunkte und 6 Bonuspunkte inklusive **konkreter Screenshots und Code-Snippets** als Beleg!
     - GitHub-Projekt-URL sichtbar auf den Folien angeben.
  2. `video_recording_group_XX.mp4`:
     - Exakte Dauer einhalten: **`Anzahl Gruppenmitglieder × 5 Minuten`**.
     - Frei gesprochen auf Basis der PDF-Folien (kein stummes Durchscrollen von Notebooks!), inklusive Vorstellung der AI-Reflexion.
  3. `materials_group_XX.zip`:
     - Ausgeführte Notebooks (`01`–`03`), `src/`, `sql/`, `data/export/*.csv`, `requirements.txt`, `README.md`, `docs/AI_USAGE.md` (aber **ohne** `.env` und `.venv`!).

---

## 6. Git-Workflow für Team & Agents

1. Immer auf dem eigenen Feature-/Dev-Branch arbeiten (`git checkout dev-<name>`).
2. Vor jedem Commit Pflichtcheck ausführen:
   ```bash
   git status
   # Prüfen: .env darf NIEMALS auftauchen! Keine riesigen HTML-Caches committen!
   ```
3. Vor einem Merge/PR nach `main`:
   - `python src/db.py` (non-destruktiver Check) fehlerfrei.
   - Geänderte Skripte (`python -m src.load_bfs`, `python -m src.scrape_tm`) oder Notebooks komplett ausgeführt.
   - `docs/AI_USAGE.md` und Status-Checkboxen in [ROADMAP.md](./ROADMAP.md) aktualisiert.
