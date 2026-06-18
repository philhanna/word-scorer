# word-scorer

Creates a dictionary of words scored for acceptability in crossword puzzles.

## How it works

The score for a word is based on how often it has appeared as an answer in
published crosswords. The more a word has been used, the more "acceptable" it
is presumed to be. [score_words.py](score_words.py) builds the dictionary in
four steps:

1. **Download the clue corpus.** It fetches the [xd crossword clue
   archive](https://xd.saul.pw/xd-clues.zip) and reads `xd/clues.tsv`, which
   contains one row per clue/answer ever published in the corpus.

2. **Count usage per answer.** The clues are grouped by answer to get a `count`
   of how many times each word has been used, and the `answer` column is
   renamed to `word`.

3. **Filter to plain words.** Only answers made up entirely of uppercase ASCII
   letters (`A`–`Z`) are kept. Entries with digits, punctuation, or
   non-English characters are discarded.

4. **Assign a log-scaled score.** Word usage follows Zipf's law: a handful of
   words are used constantly while most are used rarely. A raw count would make
   common words dominate, so the score is log-scaled:

   ```
   score = ln(count + 1) / ln(count_max + 1)
   ```

   This reflects diminishing returns — once a publisher has used a word a few
   times it is "acceptable," and using it 100 more times doesn't make it
   drastically more so. The most-used word scores `1.0`; every other word falls
   between `0` and `1`.

The result is written to `scored_words.csv` with columns `word`, `count`, and
`score`.

## Installation

Install the project (and its `numpy`, `pandas`, and `requests` dependencies,
declared in [pyproject.toml](pyproject.toml)) into your environment:

```bash
pip install .
```

This also provides a `score-words` console command.

## Usage

Once installed, run the console command:

```bash
score-words                 # writes scored_words.csv
score-words -o mywords.csv  # choose the output file name
```

Or run the script directly without installing (you'll need the dependencies):

```bash
python score_words.py -o mywords.csv
```
