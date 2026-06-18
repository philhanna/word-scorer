"""Create a dictionary of words scored for acceptability in crossword puzzles.

Downloads the xd crossword clue corpus, counts how often each answer has
been used, and assigns each word a log-scaled acceptability score.
"""

import argparse
import io
import re
import zipfile

import numpy as np
import pandas as pd
import requests

URL = "https://xd.saul.pw/xd-clues.zip"
FILE_IN_ZIP = "xd/clues.tsv"
OUTPUT_CSV = "scored_words.csv"


def main():
    args = parse_args()
    run(args.output)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "-o",
        "--output",
        default=OUTPUT_CSV,
        help=f"output CSV file name (default: {OUTPUT_CSV})",
    )
    return parser.parse_args()


def run(output_csv=OUTPUT_CSV):
    df = load_clues(URL, FILE_IN_ZIP)
    df = count_answers(df)
    df = filter_ascii_words(df)
    df = add_scores(df)
    df.to_csv(output_csv, index=False)
    print(f"df saved to {output_csv}")


def load_clues(zip_url, file_in_zip):
    """Download the zip and read the given TSV member into a DataFrame."""
    response = requests.get(zip_url)
    response.raise_for_status()

    zip_file_object = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_file_object, "r") as zf:
        with zf.open(file_in_zip) as f:
            tsv_content = f.read().decode("utf-8")

    df = pd.read_csv(io.StringIO(tsv_content), sep="\t", on_bad_lines="warn")
    print(
        f"Successfully loaded '{file_in_zip}' into a DataFrame "
        f"with {len(df)} rows and {len(df.columns)} columns."
    )
    return df


def count_answers(df):
    """Collapse clues to one row per answer with a usage count."""
    df = df.groupby(["answer"]).size().reset_index(name="count")
    df = df.rename(columns={"answer": "word"})
    return df


def filter_ascii_words(df):
    """Keep only words that are entirely uppercase ASCII letters A-Z."""
    mask = df["word"].apply(
        lambda x: isinstance(x, str) and bool(re.fullmatch(r"[A-Z]+", x))
    )
    return df[mask].copy()


def add_scores(df):
    """Add a log-scaled frequency score (the "diminishing returns" score).

    Score = ln(count + 1) / ln(count_max + 1), so the most-used word scores 1.0.
    """
    df["score"] = np.log(df["count"] + 1) / np.log(df["count"].max() + 1)
    return df


if __name__ == "__main__":
    main()
