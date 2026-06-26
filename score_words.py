"""Creates a dictionary of words scored for acceptability in crossword puzzles.

Downloads the xd crossword clue corpus, counts how often each answer has
been used, and assigns each word a log-scaled acceptability score.
"""

import argparse
import logging
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

# Module-level logger; configured in main() so the script can also be
# imported without hijacking the importer's logging setup.
logger = logging.getLogger(__name__)


def main():
    """Parse command-line arguments and run the scoring pipeline."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
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
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable debug-level logging",
    )
    return parser.parse_args()


def run(output_csv=OUTPUT_CSV):
    """Run the full pipeline and write the scored words to ``output_csv``.

    Downloads the clue corpus, reduces it to one scored row per word, and
    saves the result as a CSV with ``word``, ``count``, and ``score`` columns.

    Args:
        output_csv: Path of the CSV file to write.
    """
    logger.info("Starting word-scoring pipeline")
    df = load_clues(URL, FILE_IN_ZIP)
    df = filter_ascii_words(df)
    df = count_answers(df)
    df = add_scores(df)
    logger.info("Writing %d scored words to %s", len(df), output_csv)
    df.to_csv(output_csv, index=False)
    logger.info("Done")


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
    logger.info("Downloading clue corpus from %s", zip_url)
    response = requests.get(zip_url)
    response.raise_for_status()  # Surface 4xx/5xx as an exception.
    logger.debug("Downloaded %d bytes", len(response.content))

    # Wrap the in-memory bytes so zipfile can treat them as a file.
    logger.info("Extracting '%s' from the archive", file_in_zip)
    zip_file_object = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_file_object, "r") as zf:
        with zf.open(file_in_zip) as f:
            tsv_content = f.read().decode("utf-8")

    # on_bad_lines="skip" silently drops malformed rows instead of aborting.
    df = pd.read_csv(io.StringIO(tsv_content), sep="\t", on_bad_lines="skip")
    logger.info(
        "Loaded '%s' into a DataFrame with %d rows and %d columns",
        file_in_zip,
        len(df),
        len(df.columns),
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
    logger.info("Collapsed clues to %d distinct words", len(df))
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
    filtered = df[mask].copy()
    logger.info(
        "Kept %d of %d words after filtering to A-Z (dropped %d)",
        len(filtered),
        len(df),
        len(df) - len(filtered),
    )
    return filtered


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
    count_max = df["count"].max()
    df["score"] = np.log(df["count"] + 1) / np.log(count_max + 1)
    logger.info(
        "Scored %d words (max count %d scores 1.0)", len(df), count_max
    )
    return df


if __name__ == "__main__":
    main()
