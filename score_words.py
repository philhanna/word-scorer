"""Creates a dictionary of words scored for acceptability in crossword puzzles.

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

# Source corpus: a zip of every clue/answer published in the xd archive.
URL = "https://xd.saul.pw/xd-clues.zip"
# Path of the tab-separated clue file inside that zip.
FILE_IN_ZIP = "xd/clues.tsv"
# Default destination for the scored-word dictionary.
OUTPUT_CSV = "scored_words.csv"


def main():
    """Parse command-line arguments and run the scoring pipeline."""
    args = parse_args()
    run(args.output)


def parse_args():
    """Build the command-line parser and return the parsed arguments.

    The parser description reuses the first line of this module's docstring
    so the ``--help`` summary stays in sync with the module documentation.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "-o",
        "--output",
        default=OUTPUT_CSV,
        help=f"output CSV file name (default: {OUTPUT_CSV})",
    )
    return parser.parse_args()


def run(output_csv=OUTPUT_CSV):
    """Run the full pipeline and write the scored words to ``output_csv``.

    Downloads the clue corpus, reduces it to one scored row per word, and
    saves the result as a CSV with ``word``, ``count``, and ``score`` columns.

    Args:
        output_csv: Path of the CSV file to write.
    """
    df = load_clues(URL, FILE_IN_ZIP)
    df = count_answers(df)
    df = filter_ascii_words(df)
    df = add_scores(df)
    df.to_csv(output_csv, index=False)
    print(f"df saved to {output_csv}")


def load_clues(zip_url, file_in_zip):
    """Download a zip archive and read one TSV member into a DataFrame.

    Args:
        zip_url: URL of the zip archive to download.
        file_in_zip: Path of the TSV member to read from the archive.

    Returns:
        A DataFrame of the raw clues; each row is a single published clue,
        including its ``answer`` column.

    Raises:
        requests.HTTPError: If the download returns an error status code.
    """
    response = requests.get(zip_url)
    response.raise_for_status()  # Surface 4xx/5xx as an exception.

    # Wrap the in-memory bytes so zipfile can treat them as a file.
    zip_file_object = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_file_object, "r") as zf:
        with zf.open(file_in_zip) as f:
            tsv_content = f.read().decode("utf-8")

    # on_bad_lines="warn" skips malformed rows instead of aborting the load.
    df = pd.read_csv(io.StringIO(tsv_content), sep="\t", on_bad_lines="warn")
    print(
        f"Successfully loaded '{file_in_zip}' into a DataFrame "
        f"with {len(df)} rows and {len(df.columns)} columns."
    )
    return df


def count_answers(df):
    """Collapse the clue rows to one row per answer with a usage count.

    Args:
        df: Raw clues DataFrame containing an ``answer`` column.

    Returns:
        A DataFrame with a ``word`` column (the former ``answer``) and a
        ``count`` of how many times each word appeared as an answer.
    """
    df = df.groupby(["answer"]).size().reset_index(name="count")
    df = df.rename(columns={"answer": "word"})
    return df


def filter_ascii_words(df):
    """Keep only words made up entirely of uppercase ASCII letters A-Z.

    Drops entries containing digits, punctuation, spaces, or non-ASCII
    characters, as well as any non-string values.

    Args:
        df: DataFrame with a ``word`` column.

    Returns:
        A copy of ``df`` filtered to plain A-Z words.
    """
    mask = df["word"].apply(
        lambda x: isinstance(x, str) and bool(re.fullmatch(r"[A-Z]+", x))
    )
    # .copy() detaches the slice so later assignments don't warn or alias df.
    return df[mask].copy()


def add_scores(df):
    """Add a log-scaled frequency score (the "diminishing returns" score).

    Word usage follows Zipf's law: a few words appear constantly while most
    appear rarely. A raw count would let common words dominate, so the score
    is log-scaled and normalized against the most-used word::

        score = ln(count + 1) / ln(count_max + 1)

    The +1 keeps the logarithm defined for a count of zero. The most-used
    word scores 1.0; every other word falls between 0 and 1.

    Args:
        df: DataFrame with a ``count`` column.

    Returns:
        The same DataFrame with a new ``score`` column.
    """
    df["score"] = np.log(df["count"] + 1) / np.log(df["count"].max() + 1)
    return df


if __name__ == "__main__":
    main()
