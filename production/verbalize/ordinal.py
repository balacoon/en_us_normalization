"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes ordinal numbers
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import SIGMA


class OrdinalFst(BaseFst):
    """
    Finite state transducer for verbalizing ordinal.
    It pretty much reuses verbalization from cardinal, rewriting last word or only ending of it.
    If number ends with 1-9 or 12, the whole last word has to be modified. This is done using mapping from files:

    - ordinals/digit.tsv
    - ordinals/teen.tsv

    For others, grammar just appends "th" or rewrites "ty" to "tieth".

    Examples of input/output strings:

    - ordinal|order:13| -> thirteenth
    - ordinal|order:21| -> twenty first

    """

    def __init__(self, cardinal: CardinalFst = None):
        """
        constructor of ordinal verbalization transducer

        Parameters
        ----------
        cardinal: CardinalFst
            reusing cardinal to expand numbers to words.
        """
        super().__init__(name="ordinal")
        if cardinal is None:
            cardinal = CardinalFst()

        # replace suffix in cardinal pretrained fst
        digit = pynini.string_file(get_data_file_path("ordinals", "digit.tsv")).invert()
        teens = pynini.string_file(get_data_file_path("ordinals", "teen.tsv")).invert()
        suffix = digit | teens
        suffix |= pynutil.add_weight(pynini.cross("ty", "tieth"), weight=0.001)
        suffix |= pynutil.insert("th", weight=0.01)
        suffix = pynini.cdrewrite(suffix, "", "[EOS]", SIGMA).optimize()

        self.ordinal_far = cardinal.get_cardinal_expanding_fst() @ suffix
        graph = pynutil.delete("order:") + self.ordinal_far + pynutil.delete("|")
        self.fst = self.delete_tokens(graph).optimize()

    def get_ordinal_expanding_fst(self):
        """
        helper function that provides and fst to expand
        ordinals. can be reused by other semiotic classes.
        simply attach to your own FST or cross with permissive FST
        to limit number of digits for expansion.
        """
        return self.ordinal_far
