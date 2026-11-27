# Dokumentation des AI-Einsatzes (AI Usage Reflection)

> **Zweck dieses Dokuments:** Laufendes Pflichtprotokoll gemäss [TASK_DESCRIPTION.md](../TASK_DESCRIPTION.md) (*Minimum requirement: Documentation of AI usage for creating the code and the presentation, including advantages, disadvantages, and where something did not work with the help of AI*).  
> **Regel für Team & Agents:** Nach jedem Arbeitspaket eine neue Zeile in Abschnitt 2 ergänzen und konkrete Stärken sowie **Fehlversuche / Nachbesserungen** festhalten. Diese Punkte fliessen direkt in die Abschlussfolien und das Präsentationsvideo ein.

---

## 1. Übersicht der eingesetzten AI-Tools & Modelle

| AI-Tool / Umgebung | Modell(e) | Haupteinsatzgebiet |
| :--- | :--- | :--- |
| Google Gemini / AI Chat | **Gemini Argon** | Initiales Projekt-Scaffolding, PostgreSQL-Datenbankschema, Neon-DB-Anbindung, erster BFS-Datenloader (`main`-Branch / PR #1) & Team Onboarding Guide |
| VS Code (GitHub Copilot SDK) | **Copilot Agent** | Review & Abgleich von Onboarding-PDF, Modulvorgaben (`TASK_DESCRIPTION.md`) und technischer Spezifikation (`ROADMAP.md`) |

---

## 2. Chronologisches AI-Einsatzprotokoll

| Zeitraum / Commit | Aufgabe & betroffene Dateien | AI-Tool / Modell | Vorteile (Was gut funktionierte) | Nachteile / Wo AI versagt hat & manuelle Nacharbeit nötig war |
| :--- | :--- | :--- | :--- | :--- |
| **21.11.–27.11.2026** (`main`, PR #1: `d775f02`, `8160e35`, `07b1c78`) | **Projekt-Setup, DB-Schema & BFS-Basis-Loader:** [sql/schema.sql](../sql/schema.sql), [src/db.py](../src/db.py), [src/load_bfs.py](../src/load_bfs.py), Projektstruktur & Onboarding-PDF | **Gemini Argon** | - Sehr schneller Entwurf eines sauberen relationalen 3-Tabellen-Schemas (`municipalities`, `clubs`, `players`) inkl. Fremdschlüsseln und Indizes für Neon PostgreSQL.<br>- Funktionierende SQLAlchemy-Anbindung mit `.env`-Konfiguration.<br>- Robuste Hilfsfunktionen für heterogene BFS-/SDMX-CSVs (automatische Trennzeichen-Erkennung `;` vs. `,`, Bereinigung von Schweizer Tausendertrennzeichen `'`/`’`, Herausfiltern von Nicht-Gemeinde-Codes wie `'CH'` oder Bezirken `'B_1910'`) sowie idempotentes `ON CONFLICT (bfs_id) DO UPDATE` mit `COALESCE`. | - **Destruktiver Nebeneffekt im Verbindungstest:** In [src/db.py](../src/db.py) rief der generierte `__main__`-Block direkt `run_sql_file("sql/schema.sql")` (inkl. `DROP TABLE ... CASCADE`) auf, während das Onboarding-PDF `python src/db.py` als harmlosen Verbindungstest für Teammitglieder empfahl → Risiko, die geteilte Cloud-DB unbeabsichtigt zu löschen.<br>- **Unvollständiges Initial-Schema:** Die Spalte `area_km2` fehlte im ersten Entwurf (`8160e35`) und musste in einem Folge-Commit (`07b1c78`) nachgezogen werden.<br>- **Domänen-Vereinfachung bei Sprachregionen:** Zweisprachige Kantone (`BE`, `FR`, `VS`, `GR`) wurden in `CANTON_TO_LANG` pauschal einer einzigen Sprache zugewiesen, und 6 Schema-Spalten blieben zunächst `None`.<br>- Leere Platzhalter-Dateien (`requirements.txt`, `.env.example`) wurden angelegt, aber noch nicht befüllt. |
| **27.11.2026** (`dev-rueegsi7`) | **Anforderungs-Audit & Agent-Spezifikation:** [ROADMAP.md](../ROADMAP.md), [docs/AI_USAGE.md](./AI_USAGE.md) | **VS Code Copilot Agent** | - Systematischer Abgleich zwischen Onboarding-PDF, bestehendem Code und ZHAW-Bewertungsraster ([TASK_DESCRIPTION.md](../TASK_DESCRIPTION.md)).<br>- Aufdecken versteckter Punkte-Lücken (fehlende Karten-Visualisierung trotz Geodaten, explizite Nennung von $\chi^2$/ANOVA mit `p-value`, Join-Verlustbilanz, Moodle-Datenexport & Pflicht-Appendix). | - PDF-Anhänge konnten vom Sprachmodell nicht direkt als Binärdatei gelesen werden und mussten über ein lokales Python-/CLI-Textextraktionsskript ausgewertet werden. |

---

## 3. Zusammenfassung für die Abschlusspräsentation (laufend ergänzen)

### Wichtigste Vorteile des AI-Einsatzes
- Rasches Prototyping von Boilerplate-Code (SQL-DDL, SQLAlchemy-Engine, Upsert-Statements).
- Gute Unterstützung beim Parsen uneinheitlicher Behörden-Formate (BFS SDMX-Exporte, Zahlenformate).
- Strukturierungshilfe beim Abgleich technischer Arbeitspakete mit formalen Bewertungskriterien.

### Wichtigste Grenzen & Risiken (Lessons Learned)
- **Kontextübergreifende Konsistenz:** AI generierte in [src/db.py](../src/db.py) einen Schema-Reset beim Direktaufruf und empfahl gleichzeitig denselben Befehl in der Dokumentation als blossen Verbindungstest.
- **Schweizer Domänenwissen:** Feinheiten wie zweisprachige Kantone/Gemeinden (*Biel/Bienne*, *Fribourg*, *Oberwallis vs. Unterwallis*), ausländische Gastklubs in Schweizer Ligen (*FC Vaduz*) oder abweichende Stadiongemeinden (*Servette FC → Lancy*) erkennt AI oft nicht von selbst und erfordern explizite fachliche Kontrolle.
