"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes roman numbers
"""

import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from en_us_normalization.production.verbalize.ordinal import OrdinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import NOT_BAR, insert_space


class RomanFst(BaseFst):
    """
    Finite state transducer for verbalizing roman numerals.
    By default, romans are expanded as cardinals.
    But for some prefixes, they should be expanded as ordinals (for ex. georg the first).
    This distinction happens during tagging, verbalizer just applies expansion
    depending on the field name (count or order). Prefixes are coming from pre-defined list
    and do not require verbalization.

    Examples of input/output strings:

    - roman|count:25| -> twenty five
    - roman|prefix:chapter|count:26| -> chapter twenty six
    - roman|prefix:george|order:1| -> george the first

    """

    def __init__(self, cardinal: CardinalFst = None, ordinal: OrdinalFst = None):
        """
        constructor for roman numerals verbalizer

        Parameters
        ----------
        cardinal: CardinalFst
            reusing cardinal verbalizer, this is the one mostly applied
        ordinal: OrdinalFst
            reusing ordinal verbalizer. applied only with specific prefixes
        """
        super().__init__(name="roman")
        if cardinal is None:
            cardinal = CardinalFst()
        if ordinal is None:
            ordinal = OrdinalFst(cardinal)

        prefix = (
            pynutil.delete("prefix:")
            + pynini.closure(NOT_BAR)
            + pynutil.delete("|")
            + insert_space
        )
        # prefix is optional
        optional_prefix = pynini.closure(prefix, 0, 1)

        cardinal_roman = (
            pynutil.delete("count:") + cardinal.get_cardinal_expanding_fst()
        )
        ordinal_roman = (
            pynutil.insert("the ")
            + pynutil.delete("order:")
            + ordinal.get_ordinal_expanding_fst()
        )
        graph = cardinal_roman | ordinal_roman
        graph = optional_prefix + graph + pynutil.delete("|")
        self.fst = self.delete_tokens(graph).optimize()
