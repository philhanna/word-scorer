"""Extracts the word column from a scored-words CSV into its own file.
"""

import argparse
import logging
import pandas as pd

# Default source of scored words.
INPUT_CSV = "scored_words.csv"

# Default destination for the extracted word list.
OUTPUT_TXT = "words.txt"

# Module-level logger; configured in main() so the script can also be
# imported without hijacking the importer's logging setup.
logger = logging.getLogger(__name__)


def main():
    """Parse command-line arguments and run the extraction."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run(args.input, args.output)


def parse_args():
    """Build the command-line parser and return the parsed arguments."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "-i",
        "--input",
        default=INPUT_CSV,
        help=f"input CSV file name (default: {INPUT_CSV})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=OUTPUT_TXT,
        help=f"output file name (default: {OUTPUT_TXT})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable debug-level logging",
    )
    return parser.parse_args()


def run(input_csv=INPUT_CSV, output_txt=OUTPUT_TXT):
    """Extract the ``word`` column from ``input_csv`` and write it to ``output_txt``.

    Args:
        input_csv: Path of the scored-words CSV to read.
        output_txt: Path of the file to write the words to, one per line.
    """
    logger.info("Reading words from %s", input_csv)
    df = pd.read_csv(input_csv, usecols=["word"])
    logger.info("Writing %d words to %s", len(df), output_txt)
    df.to_csv(output_txt, index=False, header=False)
    logger.info("Done")


if __name__ == "__main__":
    main()
