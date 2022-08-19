"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify ordinals
"""

import pynini
from classify.cardinal import CardinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import DIGIT


class OrdinalFst(BaseFst):
    """
    Finite state transducer for classifying ordinal, i.e. cardinals with suffix
    In english there are just 4 suffixes to take of:

    - st - follows "1"
    - nd - follows "2"
    - rd - follows "3"
    - th - follows all the other digits. Also used for 11, 12, 13.

    Examples of input and tagged strings:

    - 13th -> ordinal { order: "13" }
    - 23rd -> ordinal { order: "23" }

    """

    def __init__(self, cardinal: CardinalFst = None):
        """
        constructor of ordinal transducer

        Parameters
        ----------
        cardinal: CardinalFst
            transducer to reuse to accept numbers
            if not provided, instantiated from scratch
        """
        super().__init__(name="ordinal")
        if cardinal is None:
            cardinal = CardinalFst()
        teens = "1" + DIGIT + pynutil.delete("th")
        first = "1" + pynutil.delete("st")
        second = "2" + pynutil.delete("nd")
        third = "3" + pynutil.delete("rd")
        nth = (DIGIT - "1" - "2" - "3") + pynutil.delete("th")
        ordinal_suffix = teens | first | second | third | nth
        ordinal_digits = pynini.closure(DIGIT | ",") + ordinal_suffix
        digits = ordinal_digits @ cardinal.get_digits_fst()
        digits_tagged = pynutil.insert('order: "') + digits + pynutil.insert('"')
        final_graph = self.add_tokens(digits_tagged)
        self.fst = final_graph.optimize()
