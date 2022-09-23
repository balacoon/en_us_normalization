"""
Copyright Balacoon 2022
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenizes and classifies abbreviations
"""

from typing import List

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_csv
from learn_to_normalize.grammar_utils.shortcuts import LOWER, TO_LOWER, TO_UPPER, UPPER


class LettersSequence:
    """
    Helper transducer which defines sequence of letters (upper or lower case),
    when all elements of that sequence are vowels or consonants
    """

    # not including y.
    # it is consonant, but it may act as vowel, for ex.: "my", "by"
    CONSONANTS = "bcdfghjklmnpqrstvwxz"
    VOWELS = "aeiou"

    def __init__(self):
        self.uppercase_vowels_fst = self.uppercase_letters_acceptor(self.VOWELS)
        self.lowercase_vowels_fst = self.lowercase_letters_acceptor(self.VOWELS)
        self.consonants_fst = self.letters_acceptor(self.CONSONANTS)

    @staticmethod
    def lowercase_letters_acceptor(letters: List[str]) -> pynini.FstLike:
        """
        accepts all the letters from the list as lowercase and converts them to upper
        """
        return pynini.union(
            *[pynini.accep(x.lower()) @ pynini.closure(TO_UPPER) for x in letters]
        )

    @staticmethod
    def uppercase_letters_acceptor(letters: List[str]) -> pynini.FstLike:
        """
        accepts all the letters from the list as uppercase
        """
        return pynini.union(*[pynini.accep(x.upper()) for x in letters])

    @staticmethod
    def letters_acceptor(letters: List[str]) -> pynini.FstLike:
        """
        Accepts either lowercase or uppercase letters from the list, where lower case letters are converted to
        upper, uppers are left intact
        """
        return LettersSequence.lowercase_letters_acceptor(
            letters
        ) | LettersSequence.uppercase_letters_acceptor(letters)


class UnpronouncableLettersSequence:
    """
    Helper transducer which loads ngrams of characters which are not common in regular words
    and is used to recognized OOV abbreviations. This is not very reliable method, so
    it is applied only for sequences of characters which are upper-case in the text.
    """

    def __init__(self):
        ngrams = load_csv(get_data_file_path("abbreviations", "ngrams.tsv"))
        ngrams_fsts_with_prefix = (
            []
        )  # unpronounceable sequence is at the end of the word
        ngrams_fsts_with_suffix = (
            []
        )  # unpronounceable sequence is at the beginning of the word
        ngrams_fsts_with_both = []  # unpronounceable sequence is anywhere in the word
        for letters in ngrams:
            # "^" and "$" marks beginning and end of the word respectively
            fst = pynini.accep(letters.strip("^$"))
            if letters.startswith("^"):
                ngrams_fsts_with_suffix.append(fst)
            elif letters.endswith("$"):
                ngrams_fsts_with_prefix.append(fst)
            else:
                ngrams_fsts_with_both.append(fst)
        all = []
        # adding closure for each ngram individually is very slow
        if ngrams_fsts_with_prefix:
            ngrams_fsts_with_prefix = pynini.union(*ngrams_fsts_with_prefix)
            ngrams_fsts_with_prefix = pynini.closure(UPPER) + ngrams_fsts_with_prefix
            all.append(ngrams_fsts_with_prefix)
        if ngrams_fsts_with_suffix:
            ngrams_fsts_with_suffix = pynini.union(*ngrams_fsts_with_suffix)
            ngrams_fsts_with_suffix = ngrams_fsts_with_suffix + pynini.closure(UPPER)
            all.append(ngrams_fsts_with_suffix)
        if ngrams_fsts_with_both:
            ngrams_fsts_with_both = pynini.union(*ngrams_fsts_with_both)
            ngrams_fsts_with_both = (
                pynini.closure(UPPER) + ngrams_fsts_with_both + pynini.closure(UPPER)
            )
            all.append(ngrams_fsts_with_both)
        self.fst = pynini.union(*all).optimize()


class AbbreviationFst(BaseFst):
    """
    Grammar for classifying abbreviations e.g.:

    - F.B.I. -> word: "FBI"
    - f.b.i. -> word: "FBI"
    - AI -> word: "AI"

    The convention is that text normalization generally returns normalized text in lower case,
    but words that needs to be spelled (pronounced letter by letter) are capitalized.
    There is no extra verbalization needed for abbreviation (apart from custom pronunciation generation),
    thus after classification, abbreviations are marked as regular words and are not passed for verbalization.

    Rules to detect abbreviations:

    1. Classic abbreviation - letters separated by dots
       upper or lower case, starting from a single letter
       for ex. f. or F.B.I.
    2. Consonants abbreviation - word contains only consonants
       (except "y"). This can't be pronounced and should be spelled.
    3. Vowels abbreviation - word contains only vowels. The rule is more
       cautious however than for consonants. It affects only sequences
       of 3 letters and sequences of 2 letters if those are upper case.
       This is done to keep "a", "i", "oi" as is.
    4. Acronyms - smth that may look like abbreviation, but is actually
       pronounced as a regular word. For example, "NATO" or "NASA".
       This is essentially exceptions that are anti-abbreviations.
       Those are recognized using list from abbreviations/acronyms.tsv
    5. Cased abbreviations - some abbreviations only make sense when
       they are in a specific case. For example "US" - is a country, while "us" is a regular word.
       Those are recognized using list from abbreviations/abbreviations_cased.tsv
    6. abbreviations - some abbreviations are case-independent as should be recognized as abbreviation
       in any case, for example "usa". Those are recognized using list from abbreviations/abbreviations.tsv
    7. unpronounceable sequences - some sequences of letters are simply unpronounceable and they indicate that
       the whole word should be spelled. List of letter n-grams that can't be pronounced is in
       abbreviations/ngrams.tsv. This rule is only applied to upper-case words.
    8. ampersand abbreviation - words with upper case letters and "&" in the middle is an abbreviation, for example:
       "AT&T"
    """

    def __init__(self):
        super().__init__(name="abbreviation")
        letters_sequence = LettersSequence()

        # 1. classic dot-separated abbreviation
        delete_dot = pynutil.delete(".")
        dot_abbr = pynini.closure((UPPER | (LOWER @ TO_UPPER)) + delete_dot, 1)

        # 2. consonants abbreviation. it can have punctuation symbols inside of it,
        # and still should be classified as abbreviation since it can't be pronounced.
        punct_symbols = "\"|/\\%!~_$()'.,"
        punct_symbols_del = [pynutil.delete(x) for x in punct_symbols]
        optional_punct_del = pynini.closure(pynini.union(*punct_symbols_del))
        consonant_abbr = letters_sequence.consonants_fst + pynini.closure(optional_punct_del + letters_sequence.consonants_fst)

        # 3. vowels abbreviation
        vowel_abbr = pynini.closure(
            letters_sequence.uppercase_vowels_fst, 2
        ) | pynini.closure(letters_sequence.lowercase_vowels_fst, 3)

        # 4. acronyms
        acronyms_lst = load_csv(get_data_file_path("abbreviations", "acronyms.tsv"))
        acronyms_vocab_abbr = pynini.union(
            *[pynini.accep(x) @ pynini.closure(TO_LOWER) for x in acronyms_lst]
        )

        # 5. cased abbreviations
        cased_abbr_lst = load_csv(
            get_data_file_path("abbreviations", "abbreviations_cased.tsv")
        )
        to_upper_or_accep = pynini.closure(UPPER | (LOWER @ TO_UPPER))
        cased_vocab_abbr = pynini.union(
            *[pynini.accep(x) @ to_upper_or_accep for x in cased_abbr_lst]
        )

        # 6. abbreviations
        abbr_lst = load_csv(get_data_file_path("abbreviations", "abbreviations.tsv"))
        abbr_fsts_lst = []
        for abbr in abbr_lst:
            # sequence of characters: lower converted to upper or just upper
            seq = [
                pynini.accep(x.lower()) @ TO_UPPER | pynini.accep(x.upper())
                for x in abbr
            ]
            seq_fst = seq[0]
            for element in seq[1:]:
                seq_fst += element
            abbr_fsts_lst.append(seq_fst)
        vocab_abbr = pynini.union(*abbr_fsts_lst)

        # 7. unpronounceable sequences
        unpron_abbr = UnpronouncableLettersSequence().fst

        # 8. ampersand abbreviation
        and_abbr = (
            pynini.closure(UPPER, 1)
            + pynini.cross("&", " and ")
            + pynini.closure(UPPER, 1)
        )

        # abbreviation may have a suffix, for ex s, 's or 'S
        s = pynini.cross("s", "'S")
        s |= pynini.accep("'") + pynini.union(pynini.accep("S"), pynini.cross("s", "S"))
        optional_suffix = pynini.closure(s, 0, 1)

        abbr = (
            dot_abbr
            | consonant_abbr
            | vowel_abbr
            | acronyms_vocab_abbr
            | cased_vocab_abbr
            | vocab_abbr
            | unpron_abbr
            | and_abbr
        )
        graph = abbr + optional_suffix
        graph = pynutil.insert('name: "') + graph + pynutil.insert('"')
        self._single_fst = graph.optimize()
        self.connect_to_self(connector_in="/", connector_out=None, connector_spaces="none")
