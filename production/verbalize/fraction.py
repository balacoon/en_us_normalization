"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes fractions
"""

import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from en_us_normalization.production.verbalize.ordinal import OrdinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import SIGMA, insert_space


class FractionFst(BaseFst):
    """
    Finite state transducer for verbalizing fraction.
    Fraction consists of integer part, numerator and denominator.
    To expand integer part and numerator - cardinal transducer is reused.
    For denominator of the fraction however - ordinal transducer is needed.

    There are few exception, when fraction (both numerator and denominator) is
    expanded as one word (for ex. 1/2 -> half)

    Also some denominators (2, 3, 4) require custom expansion (halves, thirds, quarters).

    When either numerator or denominator are "1" - this is also a special cases
    that has to be handled explicitly.

    Examples of input/output strings:

    - fraction|integer_part:23|numerator:4|denominator:5| -> twenty three and four fifths

    """

    def __init__(self, cardinal: CardinalFst = None, ordinal: OrdinalFst = None):
        super().__init__(name="fraction")
        if cardinal is None:
            cardinal = CardinalFst()
        if ordinal is None:
            ordinal = OrdinalFst(cardinal=cardinal)

        # custom denominators are 1, 2, 3 and 4.
        # they are expanded differently then the rest.
        custom_denominator = (
            pynini.cross("1", "over one")
            | pynini.cross("2", "halves")
            | pynini.cross("3", "thirds")
            | pynini.cross("4", "quarters")
        )
        custom_denominator = (
            pynutil.delete("denominator:") + custom_denominator + pynutil.delete("|")
        )

        # standard denominators expanded with ordinal transducer
        standard_denominator = (
            pynutil.delete("denominator:")
            + ordinal.get_ordinal_expanding_fst()
            + pynutil.delete("|")
        )

        # numerators are expanded with cardinal transducer
        standard_numerator = (
            pynutil.delete("numerator:")
            + cardinal.get_cardinal_expanding_fst()
            + pynutil.delete("|")
        )
        # custom numerator where value is "1".
        one_numerator = pynini.cross("numerator:1|", "one")

        # when numerator is "1", denominator is singular.
        # only standard denominator is handled because customs are within single word fraction
        singular_fraction = one_numerator + insert_space + standard_denominator
        # when numerator >1, standard denominator is plural, but custom one is not
        denominator = custom_denominator | pynutil.add_weight(
            standard_denominator + pynutil.insert("s"), 1.1
        )
        plural_fraction = standard_numerator + insert_space + denominator
        # custom fractions that are expanded as single word: 1/2, 1/3, 1/4
        single_word_fraction = (
            pynini.cross("2", "half")
            | pynini.cross("3", "third")
            | pynini.cross("4", "quarter")
        )
        single_word_fraction = (
            pynini.cross("numerator:1|denominator:", "a ")
            + single_word_fraction
            + pynutil.delete("|")
        )
        fraction = (
            single_word_fraction
            | pynutil.add_weight(singular_fraction, 1.05)
            | pynutil.add_weight(plural_fraction, 1.1)
        )

        # expanding integer part as cardinal
        integer = (
            pynutil.delete("integer_part:")
            + cardinal.get_cardinal_expanding_fst()
            + pynutil.delete("|")
        )
        # fraction doesn't always have integer part
        optional_integer = pynini.closure(integer + pynutil.insert(" and "), 0, 1)

        optional_sign = pynini.closure(pynini.cross("negative:1|", "minus "), 0, 1)
        graph = optional_sign + optional_integer + fraction
        # when it's a single word fraction and there is no integer part,
        # prefix should be rewritten, i.e.
        # it is "1 1/2 -> one and a half"
        # but it is "1/2 -> one half"
        only_fraction_prefix = pynini.cdrewrite(
            pynini.cross("a ", "one "), "[BOS]", "", SIGMA
        ).optimize()
        self.graph = graph @ only_fraction_prefix
        self.fst = self.delete_tokens(self.graph).optimize()

    def get_graph(self):
        """
        helper function that returns the whole fraction verbalization graph
        without token name deletion. this is needed if the whole fraction
        graph is reused in another semiotic class (for ex. measure)
        """
        return self.graph
