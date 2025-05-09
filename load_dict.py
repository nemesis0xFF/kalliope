"""
Builds dict.db for the Kalliope project.

Steps:
1. Download Lexique383.tsv (word frequencies + phonetics).
2. (Optional) Download future datasets such as Wiktionary XML.
3. Create SQLite schema with word table, relation table, FTS5 index.
4. Load French words into the database.

Run inside Docker: python load_dict.py
"""

from pathlib import Path
import sqlite3
import urllib.request
import shutil
import pandas as pd
from tqdm import tqdm
from pyphonetics import FuzzySoundex
from unidecode import unidecode

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "dict.db"

LEXIQUE_URL = (
    "https://raw.githubusercontent.com/chrplr/openLexicon/master/Lexique383.tsv"
)
LEXIQUE_TSV = DATA_DIR / "Lexique383.tsv"


def download(url: str, dest: Path) -> None:
    """Download a file only if it does not exist locally."""
    if dest.exists():
        return
    print(f"⇩ Downloading {url}")
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)


def main() -> None:
    # 1. Fetch resources
    download(LEXIQUE_URL, LEXIQUE_TSV)

    # 2. Read Lexique (tab‑separated)
    print("Parsing Lexique383.tsv …")
    df = pd.read_csv(LEXIQUE_TSV, sep="\t")
    df = df.rename(
        columns={
            "ortho": "lemma",
            "freqfilms2": "freq",
            "phon": "phonetic",
        }
    )
    df["lang"] = "fr"
    df = df[["lemma", "lang", "phonetic", "freq"]]

    # 3. Create SQLite schema
    print("Creating SQLite database …")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS word(
                id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL,
                lemma TEXT NOT NULL,
                phonetic TEXT,
                freq REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS relation(
                src_id INTEGER,
                dst_id INTEGER,
                type TEXT,
                FOREIGN KEY(src_id) REFERENCES word(id),
                FOREIGN KEY(dst_id) REFERENCES word(id)
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS word_fts
            USING fts5(lemma, content='word', content_rowid='id');
        """
    )

    # 4. Load data
    print("Inserting words …")
    df.to_sql("word", con, if_exists="append", index=False)

    # 5. Populate FTS
    print("Building full‑text index …")
    cur.execute(
        "INSERT INTO word_fts(rowid, lemma) "
        "SELECT id, lemma FROM word WHERE lang='fr';"
    )
    con.commit()
    con.close()
    print("[OK] dict.db generated successfully")


if __name__ == "__main__":
    main()
