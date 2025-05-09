"""
Builds dict.db for the Kalliope project.

Steps
-----
1. Download Lexique383.tsv (word frequencies + phonetics).
2. Create SQLite schema with word / relation tables + FTS5 index.
3. Load French words into the database.

Run inside Docker:  python load_dict.py
"""

from pathlib import Path
import sqlite3
import urllib.request
import shutil
import pandas as pd
from tqdm import tqdm
from pyphonetics import FuzzySoundex  # will be useful later
from unidecode import unidecode

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
DATA_DIR   = Path("data")
DB_PATH    = DATA_DIR / "dict.db"
LEXIQUE_URL = (
    "http://www.lexique.org/databases/Lexique383/Lexique383.tsv"
)
LEXIQUE_TSV = DATA_DIR / "Lexique383.tsv"

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def download(url: str, dest: Path) -> None:
    """Download *url* to *dest* if the file does not already exist."""
    if dest.exists():
        return
    print(f"⇩ Downloading {url}")
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

    # 1. Fetch resources
    download(LEXIQUE_URL, LEXIQUE_TSV)

    # 2. Read Lexique383
    print("Parsing Lexique383.tsv …")
    df = pd.read_csv(LEXIQUE_TSV, sep="\t")
    df.columns = df.columns.str.strip().str.lower()  # normalize headers

    # Map whichever column is present to 'lemma'
    if "ortho" in df.columns:
        df = df.rename(columns={"ortho": "lemma"})
    elif "lemme" in df.columns:
        df = df.rename(columns={"lemme": "lemma"})
    else:
        raise ValueError("Could not find a lemma column in Lexique383.tsv")

    # Rename remaining columns of interest
    df = df.rename(
        columns={
            "freqfilms2": "freq",
            "phon": "phonetic",
        }
    )

    # Add language and keep only the four columns matching the SQL schema
    df["lang"] = "fr"
    df = df.loc[:, ["lemma", "lang", "phonetic", "freq"]]

    # Data hygiene: drop bad rows, fill NaNs, deduplicate
    df = (
        df[df["lemma"].notna() & (df["lemma"].str.strip() != "")]
          .fillna({"phonetic": "", "freq": 0.0})
          .drop_duplicates(subset=["lemma", "lang"])
    )

    # 3. Create SQLite schema
    print("Creating SQLite database …")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS word (
    id       INTEGER PRIMARY KEY,
    lang     TEXT NOT NULL,
    lemma    TEXT NOT NULL,
    phonetic TEXT,
    freq     REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS relation (
    src_id INTEGER,
    dst_id INTEGER,
    type   TEXT,
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

    # 5. Populate FTS index
    print("Building full‑text index …")
    cur.execute(
        "INSERT INTO word_fts(rowid, lemma) "
        "SELECT id, lemma FROM word WHERE lang='fr';"
    )
    con.commit()
    con.close()
    print("✅ dict.db generated successfully")


if __name__ == "__main__":
    main()
"""
Builds dict.db for the Kalliope project.

Steps
-----
1. Download Lexique383.tsv (word frequencies + phonetics).
2. Create SQLite schema with word / relation tables + FTS5 index.
3. Load French words into the database.

Run inside Docker:  python load_dict.py
"""

from pathlib import Path
import sqlite3
import urllib.request
import shutil
import pandas as pd
from tqdm import tqdm
from pyphonetics import FuzzySoundex  # will be useful later
from unidecode import unidecode

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
DATA_DIR   = Path("data")
DB_PATH    = DATA_DIR / "dict.db"
LEXIQUE_URL = (
    "http://www.lexique.org/databases/Lexique383/Lexique383.tsv"
)
LEXIQUE_TSV = DATA_DIR / "Lexique383.tsv"

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def download(url: str, dest: Path) -> None:
    """Download *url* to *dest* if the file does not already exist."""
    if dest.exists():
        return
    print(f"⇩ Downloading {url}")
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)

    # 1. Fetch resources
    download(LEXIQUE_URL, LEXIQUE_TSV)

    # 2. Read Lexique383
    print("Parsing Lexique383.tsv …")
    df = pd.read_csv(LEXIQUE_TSV, sep="\t")
    df.columns = df.columns.str.strip().str.lower()  # normalize headers

    # Map whichever column is present to 'lemma'
    if "ortho" in df.columns:
        df = df.rename(columns={"ortho": "lemma"})
    elif "lemme" in df.columns:
        df = df.rename(columns={"lemme": "lemma"})
    else:
        raise ValueError("Could not find a lemma column in Lexique383.tsv")

    # Rename remaining columns of interest
    df = df.rename(
        columns={
            "freqfilms2": "freq",
            "phon": "phonetic",
        }
    )

    # Add language and keep only the four columns matching the SQL schema
    df["lang"] = "fr"
    df = df.loc[:, ["lemma", "lang", "phonetic", "freq"]]

    # Data hygiene: drop bad rows, fill NaNs, deduplicate
    df = (
        df[df["lemma"].notna() & (df["lemma"].str.strip() != "")]
          .fillna({"phonetic": "", "freq": 0.0})
          .drop_duplicates(subset=["lemma", "lang"])
    )

    # 3. Create SQLite schema
    print("Creating SQLite database …")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS word (
    id       INTEGER PRIMARY KEY,
    lang     TEXT NOT NULL,
    lemma    TEXT NOT NULL,
    phonetic TEXT,
    freq     REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS relation (
    src_id INTEGER,
    dst_id INTEGER,
    type   TEXT,
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

    # 5. Populate FTS index
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
