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
        # if there is more than punctuation ensure that we finish on non-punctuation character.
        # in that way, trailing punctuation on the right will go to punctuation.
        not_space = pynutil.add_weight(NOT_SPACE, 1.01) | pynini.cross('"', '\\"') | pynini.cross('\\', '\\\\\\')
        not_punct = pynutil.add_weight(NOT_PUNCT, 1.01) | pynini.cross('\\', '\\\\\\')
        just_punct = pynutil.add_weight(PUNCT, 1.01) | pynini.cross('"', '\\"')
        word = (not_punct + pynini.closure(not_space) + not_punct) | not_punct | pynini.closure(just_punct, 1)
        final_graph = pynutil.insert('name: "') + word + pynutil.insert('"')
        final_graph = self.add_tokens(final_graph)
        self._single_fst = final_graph.optimize()
