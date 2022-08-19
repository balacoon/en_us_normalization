"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify regular words
"""

import pynini
from english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import (
    ALPHA,
    TO_LOWER,
)


class WordFst(BaseFst):
    """
    Finite state transducer for classifying words - smth that doesn't need verbalization, i.e.
    it is already normalized and contains letters that are all known to pronunciation dictionary.
    Regular words are meant to be pronounced, so if token is classified as regular word, it is
    brought to lower case.

    Additionally, word transducer normalizes unicode letters, such as "é". Unicode characters and their
    mappings are stored in "unicode_chars.tsv"

    Examples of input/output strings:

    - sleep -> name: "sleep"
    - don't -> name: "don't"
    - Hello -> name: "hello"
    """

    def __init__(self):
        super().__init__(name="word")
        # just alpha characters that can go directly to pronunciation generation
        unicode_char = pynini.string_file(get_data_file_path("unicode_chars.tsv"))
        alpha = (
            pynutil.add_weight(ALPHA, 1.1) | pynini.accep("'") | unicode_char | TO_LOWER
        )
        word = pynini.closure(alpha, 1)
        word = pynutil.insert('name: "') + word + pynutil.insert('"')
        self.fst = word.optimize()
