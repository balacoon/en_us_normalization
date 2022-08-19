"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify verbatim
"""

import pynini
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import NOT_PUNCT, NOT_SPACE


class VerbatimFst(BaseFst):
    """
    Finite state transducer for classifying verbatims - anything that has extra symbols and doesn't
    match available semiotic classes. Verbatim takes any characters, ommitting spaces (boudnary between tokens)
    and trailing punctuation marks.

    Example of input/output string:

    - jo234 -> verbatim { name: "jo234" }

    """

    def __init__(self):
        super().__init__(name="verbatim")
        # anything is classified as verbatim with very low probability. punctuation is left out
        word = pynini.closure(NOT_PUNCT, 0) + pynini.closure(
            pynini.closure(NOT_SPACE) + NOT_PUNCT
        )
        final_graph = pynutil.insert('name: "') + word + pynutil.insert('"')
        final_graph = self.add_tokens(final_graph)
        self.fst = final_graph.optimize()
