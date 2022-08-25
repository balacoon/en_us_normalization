"""
Copyright 2022 Balacoon

small script to check if a word overlaps with
any of unpronouncable ngrams and which
"""

import os
import logging
import argparse


def parse_args():
    ap = argparse.ArgumentParser(description="Small script to check which n-gram is triggered on particular word")
    ap.add_argument("word", help="Word to check")
    args = ap.parse_args()
    return args


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    abbreviation_data_dir = os.path.dirname(os.path.abspath(__file__))
    ngrams_path = os.path.join(abbreviation_data_dir, "ngrams.tsv")
    assert os.path.isfile(ngrams_path), "Cant open {}".format(ngrams_path)
    word = args.word.upper()
    with open(ngrams_path, "r") as fp:
        for line in fp:
            ngram = line.strip()
            if ngram.startswith("^") and ngram.endswith("$"):
                logging.warning("Shouldn't have service tokens from both sides: [{}]!".format(ngram))
            if ngram.startswith("^"):
                ngram_strip = ngram[1:]
                if word.startswith(ngram_strip):
                    logging.info("{} is triggered by {}".format(ngram, word))
            elif ngram.endswith("$"):
                ngram_strip = ngram[:-1]
                if word.endswith(ngram_strip):
                    logging.info("{} is triggered by {}".format(ngram, word))
            else:
                if ngram in word:
                    logging.info("{} is triggered by {}".format(ngram, word))
    logging.info("Checked all ngrams")


if __name__ == "__main__":
    main()
