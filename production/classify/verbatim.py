"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify verbatim
"""

import pynini
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import PUNCT, NOT_PUNCT, NOT_SPACE


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
        # if its just punctuation - apply verbatim to it
        word = pynutil.add_weight(pynini.closure(PUNCT, 1), 1.1)
        # if there is more than punctuation ensure that we finish on non-punctuation character.
        # in that way, trailing punctuation on the right will go to punctuation.
        # Also need to adjust quotation marks if any, so they don't affect parsing of tokenized/tagged string
        verbatim_symbols = pynutil.add_weight(NOT_SPACE, 1.1) | pynini.cross('"', '\\"')
        word |= (pynini.closure(verbatim_symbols) + NOT_PUNCT)
        final_graph = pynutil.insert('name: "') + word + pynutil.insert('"')
        final_graph = self.add_tokens(final_graph)
        self._single_fst = final_graph.optimize()
