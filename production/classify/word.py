"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify regular words
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_union
from learn_to_normalize.grammar_utils.shortcuts import ALPHA, TO_LOWER


class WordFst(BaseFst):
    """
    Finite state transducer for classifying words - smth that doesn't need verbalization, i.e.
    it is already normalized and contains letters that are all known to pronunciation dictionary.
    Regular words are meant to be pronounced, so if token is classified as regular word, it is
    brought to lower case.

    Additionally, word transducer normalizes unicode letters, such as "é". Unicode characters and their
    mappings are stored in "unicode_chars.tsv"

    Finally, word transducer has to handle apostrophe. It's okay to have apostrophe inside the word,
    but at the beginning and at the end it can be confused with single quotation mark.
    There are few cases when apostrophe on a word boundary is justified:

    - It's a shortened version of a word. For ex. "'em" is "them"
    - Apostrophe indicates possession, for ex "Thomas' watch"

    Examples of input/output strings:

    - sleep -> name: "sleep"
    - don't -> name: "don't"
    - Hello -> name: "hello"
    """

    def __init__(self):
        super().__init__(name="word")
        # just alpha characters that can go directly to pronunciation generation
        unicode_char = pynini.string_file(get_data_file_path("unicode_chars.tsv"))
        apostrophe = pynini.accep("'")

        # regular words
        alpha = pynutil.add_weight(ALPHA, 1.1) | unicode_char | TO_LOWER
        # word with optional apostroph inside
        word = alpha + pynini.closure(alpha | apostrophe) + alpha
        # allow also single letter words
        word |= alpha

        # allow apostrophe at the end of the word if word ends with "s" or "ce"
        s_endigns = (
            pynini.accep("s'")
            | (pynini.cross("S", "s") + apostrophe)
            | pynini.accep("ce'")
            | (pynini.cross("CE", "ce") + apostrophe)
        )
        word += pynini.closure(s_endigns, 0, 1)

        # allow apostrophe in front of the word if word is from the list
        shortened_words = load_union(get_data_file_path("front_apostrophe.tsv"), case_agnostic=True)
        word |= (apostrophe + shortened_words)

        word = pynutil.insert('name: "') + word + pynutil.insert('"')
        self._single_fst = word.optimize()
