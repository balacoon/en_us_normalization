"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Entry point to tokenize and classify
"""

import pynini
from en_us_normalization.production.classify.abbreviation import AbbreviationFst
from en_us_normalization.production.classify.address import AddressFst
from en_us_normalization.production.classify.cardinal import CardinalFst
from en_us_normalization.production.classify.date import DateFst
from en_us_normalization.production.classify.decimal import DecimalFst
from en_us_normalization.production.classify.electronic import ElectronicFst
from en_us_normalization.production.classify.fraction import FractionFst
from en_us_normalization.production.classify.measure import MeasureFst
from en_us_normalization.production.classify.money import MoneyFst
from en_us_normalization.production.classify.multi_token.attached import AttachedTokensFst
from en_us_normalization.production.classify.ordinal import OrdinalFst
from en_us_normalization.production.classify.punctuation_rules import get_punctuation_rules
from en_us_normalization.production.classify.roman import RomanFst
from en_us_normalization.production.classify.shortening import ShorteningFst
from en_us_normalization.production.classify.telephone import TelephoneFst
from en_us_normalization.production.classify.time import TimeFst
from en_us_normalization.production.classify.verbatim import VerbatimFst
from en_us_normalization.production.classify.word import WordFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_extra_space, delete_space, wrap_token, TO_LOWER, LOWER, CHAR


class ClassifyFst(BaseFst):
    """
    Final class that composes all other classification grammars.
    This class can process an entire sentence including punctuation.
    For deployment, this grammar will be compiled and exported to OpenFst Finite State Archive (FAR) File.
    """

    def __init__(self):
        super().__init__(name="tokenize_and_classify")

        address = AddressFst()
        cardinal = CardinalFst()
        date = DateFst()
        word = WordFst()
        verbatim = VerbatimFst()
        time = TimeFst()
        telephone = TelephoneFst()
        electronic = ElectronicFst()
        abbreviation = AbbreviationFst()
        shortening = ShorteningFst()
        ordinal = OrdinalFst(cardinal=cardinal)
        decimal = DecimalFst(cardinal=cardinal)
        fraction = FractionFst(cardinal=cardinal)
        money = MoneyFst(decimal=decimal)
        roman = RomanFst(cardinal=cardinal)
        measure = MeasureFst(decimal=decimal, fraction=fraction)
        left_punct, right_punct = get_punctuation_rules()

        classify = (
            pynutil.add_weight(shortening.fst, 1.01)
            | pynutil.add_weight(abbreviation.fst, 1.1)
            | pynutil.add_weight(address.fst, 1.01)
            | pynutil.add_weight(time.fst, 1.1)
            | pynutil.add_weight(date.fst, 1.01)
            | pynutil.add_weight(decimal.fst, 10.0)
            | pynutil.add_weight(measure.fst, 1.1)
            | pynutil.add_weight(cardinal.fst, 9.0)
            | pynutil.add_weight(ordinal.fst, 9.0)
            | pynutil.add_weight(money.fst, 1.1)
            | pynutil.add_weight(telephone.fst, 1.1)
            | pynutil.add_weight(electronic.fst, 1.1)
            | pynutil.add_weight(fraction.fst, 10.0)
            | pynutil.add_weight(word.fst, 10)
            | pynutil.add_weight(verbatim.fst, 100)
            | pynutil.add_weight(roman.fst, 1.09)
        )
        token = wrap_token(left_punct + classify + right_punct)

        # also add multi-token taggers
        attached = AttachedTokensFst(
            cardinal, abbreviation, word, left_punct, right_punct
        )
        token |= pynutil.add_weight(attached.fst, 2.0)

        graph = token + pynini.closure(delete_extra_space + token)
        graph = delete_space + graph + delete_space
        # to enable detection of all-capitals lines - uncomment
        # graph = self._fix_all_capital_fst() @ graph
        self._single_fst = graph.optimize()

    @staticmethod
    def _fix_all_capital_fst():
        """
        helper function that detects that input text is all caps
        and converts it to lower case before feeding to main fst.
        If there is a single lower-case symbol, fst does nothing.
        """
        # accepting all characters with a little penalty
        fst = pynutil.add_weight(pynini.closure(CHAR, 1), 3.0)
        # converting all uppercase to lower, allowing any other characters but lower case
        fst |= pynini.closure(TO_LOWER | pynutil.add_weight(pynini.invert(LOWER), 1.1), 1)
        return fst
