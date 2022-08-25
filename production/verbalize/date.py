"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes dates
"""

import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from en_us_normalization.production.verbalize.ordinal import OrdinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import (
    DIGIT,
    NOT_BAR,
    SIGMA,
    insert_space,
)


class DateFst(BaseFst):
    """
    Finite state transducer for verbalization of dates.
    Reuses cardinal and ordinal FSTs to expand numbers.
    Ordinal is needed for days (for ex. fifth of february) and
    cardinal is meant to expand years. Years expansion can be tricky,
    often year is read 2 digits at a time (2012 -> twenty twelve).

    Examples of input/output strings:

    - date|month:february|day:5|year:2012| -> february fifth twenty twelve
    - date|day:5|month:february|year:2012| -> the fifth of february twenty twelve

    """

    def __init__(self, cardinal: CardinalFst = None, ordinal: OrdinalFst = None):
        super().__init__(name="date")
        if cardinal is None:
            cardinal = CardinalFst()
        if ordinal is None:
            ordinal = OrdinalFst(cardinal=cardinal)

        month = pynini.closure(
            NOT_BAR, 1
        )  # month is already expanded during classification
        month = pynutil.delete("month:") + month + pynutil.delete("|")

        day = (
            pynutil.delete("day:")
            + ordinal.get_ordinal_expanding_fst()
            + pynutil.delete("|")
        )

        # years like 1991, 2021 or 1905
        two_digits = pynini.closure(DIGIT, 2, 2) @ cardinal.get_digit_pairs_fst()
        four_digits = two_digits + insert_space + two_digits
        modern_year = pynutil.add_weight(four_digits, 1.1)

        # years like 1900
        modern_year_zeros = (
            two_digits + pynutil.delete("00") + pynutil.insert(" hundred")
        )
        modern_year_zeros = pynutil.add_weight(modern_year_zeros, 1.05)

        # years like 2001
        modern_year_mid_zeros = DIGIT + pynini.accep("00") + DIGIT
        modern_year_mid_zeros = (
            modern_year_mid_zeros @ cardinal.get_cardinal_expanding_fst()
        )
        modern_year_mid_zeros = pynutil.add_weight(modern_year_mid_zeros, 1.01)

        # years like 935
        other_years = pynini.closure(DIGIT, 1) @ cardinal.get_cardinal_expanding_fst()
        other_years = pynutil.add_weight(other_years, 10)

        # years like 09
        two_digits_year = two_digits

        year = (
            modern_year
            | modern_year_zeros
            | modern_year_mid_zeros
            | two_digits_year
            | other_years
        )
        year = pynutil.delete("year:") + year + pynutil.delete("|")

        # take care of the "s" era
        # year:1900|era:s| -> nineteen hundreds
        # year:2010|era:s| -> twenty tens
        # year:2000|era:s| -> two thousands
        # year:2020|era:s| -> twenty twentys (fixed later)
        year_era_s = year + pynutil.delete("era:") + "s" + pynutil.delete("|")

        # take care of the "bc" and others eras
        year_era = (
            year
            + pynutil.delete("era:")
            + insert_space
            + pynini.closure(NOT_BAR, 1)
            + pynutil.delete("|")
        )
        year_era = pynutil.add_weight(year_era, 1.1)

        year = year | year_era_s | year_era
        # fix tys to be ties
        year = year @ pynini.cdrewrite(pynini.cross("ys", "ies"), "t", "[EOS]", SIGMA)

        date_dmy = (
            pynutil.insert("the ")
            + day
            + pynutil.insert(" of ")
            + month
            + pynini.closure(insert_space + year, 0, 1)
        )
        date_mdy = (
            month
            + pynini.closure(insert_space + day, 0, 1)
            + pynini.closure(insert_space + year, 0, 1)
        )

        graph = date_dmy | date_mdy | year
        self._single_fst = self.delete_tokens(graph).optimize()
