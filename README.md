# word-scorer

Creates a dictionary of words scored for acceptability in crossword puzzles.

## How it works

The score for a word is based on how often it has appeared as an answer in
published crosswords. The more a word has been used, the more "acceptable" it
is presumed to be. [score_words.py](score_words.py) builds the dictionary in
six steps:

1. **Download the clue corpus.** It fetches the [xd crossword clue
   archive](https://xd.saul.pw/xd-clues.zip) and reads `xd/clues.tsv`, which
   contains one row per clue/answer ever published in the corpus. The loaded
   `answer` column is renamed to `word`.

2. **Filter to plain words.** Only answers made up entirely of uppercase ASCII
   letters (`A`–`Z`) are kept. Entries with digits, punctuation, or
   non-English characters are discarded.

3. **Add word lengths and drop short entries.** Each remaining word gets a
   `length` column, and words shorter than 3 letters are discarded.

4. **Count usage per word.** The clues are grouped by `word` and `length` to
   get a `count` of how many times each word has been used.

5. **Assign a log-scaled score.** Word usage follows Zipf's law: a handful of
   words are used constantly while most are used rarely. A raw count would make
   common words dominate, so the score is log-scaled using the number of
   distinct words of the same length as the normalization term:

   ```
   score = ln(count + 1) / ln(count_max + 1)
   ```

   Here `count_max` is the number of distinct words whose length matches the
   current word. This reflects diminishing returns — once a publisher has used
   a word a few times it is "acceptable," and using it 100 more times doesn't
   make it drastically more so.

6. **Sort the output.** The final table is sorted by `length` ascending, then
   `score` descending, then `word` ascending.

The result is written to `scored_words.csv` with columns `word`, `length`,
`count`, and `score`.

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
score-words -v              # enable debug logging
```

Or run the script directly without installing (you'll need the dependencies):

```bash
python score_words.py -o mywords.csv
python score_words.py -v
```
