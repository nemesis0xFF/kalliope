# -*- coding: utf-8 -*-
from pathlib import Path
import sqlite3
import urllib.request
import shutil
import pandas as pd
from tqdm import tqdm
from pyphonetics import FuzzySoundex
from unidecode import unidecode

# Configuration
DATA_DIR    = Path("data")
DB_PATH     = DATA_DIR / "dict.db"
LEXIQUE_URL = "http://www.lexique.org/databases/Lexique383/Lexique383.tsv"
LEXIQUE_TSV = DATA_DIR / "Lexique383.tsv"

def download(url: str, dest: Path) -> None:
    """
    Download a file from a URL to a destination path if it does not exist.
    """
    if dest.exists():
        return
    print(f"⇩ Downloading {url}")
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)

def main() -> None:
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

    # 1. Download Lexique TSV
    download(LEXIQUE_URL, LEXIQUE_TSV)

    # 2. Read and clean Lexique data
    print("Parsing Lexique383.tsv …")
    df = pd.read_csv(LEXIQUE_TSV, sep="\t")
    df.columns = df.columns.str.strip().str.lower()

    # Map the appropriate column to 'lemma'
    if "ortho" in df.columns:
        df = df.rename(columns={"ortho": "lemma"})
    elif "lemme" in df.columns:
        df = df.rename(columns={"lemme": "lemma"})
    else:
        raise ValueError("Could not find a 'lemma' column in Lexique383.tsv")

    # Rename other columns of interest
    df = df.rename(columns={
        "freqfilms2": "freq",
        "phon":       "phonetic"
    })

    # Add language tag and select only the schema columns
    df["lang"] = "fr"
    df = df.loc[:, ["lemma", "lang", "phonetic", "freq"]]

    # Data hygiene: drop rows without lemmas, fill NaNs, deduplicate
    df = (
        df[df["lemma"].notna() & (df["lemma"].str.strip() != "")]
          .fillna({"phonetic": "", "freq": 0.0})
          .drop_duplicates(subset=["lemma", "lang"])
    )

    # 3. Create SQLite schema with DELETE journal mode and standalone FTS4
    print("Creating SQLite database …")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
PRAGMA journal_mode=DELETE;

CREATE TABLE IF NOT EXISTS word (
    id       INTEGER PRIMARY KEY,
    lang     TEXT    NOT NULL,
    lemma    TEXT    NOT NULL,
    phonetic TEXT,
    freq     REAL    DEFAULT 0
);

CREATE TABLE IF NOT EXISTS relation (
    src_id INTEGER,
    dst_id INTEGER,
    type   TEXT,
    FOREIGN KEY(src_id) REFERENCES word(id),
    FOREIGN KEY(dst_id) REFERENCES word(id)
);

-- Standalone FTS4 index on lemma only
CREATE VIRTUAL TABLE IF NOT EXISTS word_fts
USING fts4(lemma);
""")

    # 4. Load words into the 'word' table
    print("Inserting words …")
    df.to_sql("word", con, if_exists="append", index=False)

    # 5. Populate the FTS4 index
    print("Building full-text index …")
    cur.execute(
        "INSERT INTO word_fts(lemma) SELECT lemma FROM word WHERE lang='fr';"
    )

    con.commit()
    con.close()
    print("[OK] dict.db generated successfully")

if __name__ == "__main__":
    main()
