"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Entry point to tokenize and classify
"""

import pynini
from classify.abbreviation import AbbreviationFst
from classify.address import AddressFst
from classify.cardinal import CardinalFst
from classify.date import DateFst
from classify.decimal import DecimalFst
from classify.electronic import ElectronicFst
from classify.fraction import FractionFst
from classify.measure import MeasureFst
from classify.money import MoneyFst
from classify.multi_token.math import MathFst
from classify.multi_token.range import RangeFst
from classify.multi_token.score import ScoreFst
from classify.ordinal import OrdinalFst
from classify.punctuation_rules import get_punctuation_rules
from classify.roman import RomanFst
from classify.shortening import ShorteningFst
from classify.telephone import TelephoneFst
from classify.time import TimeFst
from classify.verbatim import VerbatimFst
from classify.word import WordFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_extra_space, delete_space, wrap_token


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
        score = ScoreFst(cardinal)
        math = MathFst(
            cardinal, decimal, money, measure, fraction, left_punct, right_punct
        )
        fromto = RangeFst(
            cardinal,
            decimal,
            money,
            measure,
            fraction,
            date,
            time,
            roman,
            left_punct,
            right_punct,
        )
        multi_token = score.fst | math.fst | fromto.fst

        # repeating token
        token |= multi_token
        graph = token + pynini.closure(delete_extra_space + token)
        graph = delete_space + graph + delete_space

        self.fst = graph.optimize()
