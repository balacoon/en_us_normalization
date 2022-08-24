"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Entry point to verbalize
"""

from en_us_normalization.production.verbalize.address import AddressFst
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from en_us_normalization.production.verbalize.date import DateFst
from en_us_normalization.production.verbalize.decimal import DecimalFst
from en_us_normalization.production.verbalize.electronic import ElectronicFst
from en_us_normalization.production.verbalize.fraction import FractionFst
from en_us_normalization.production.verbalize.measure import MeasureFst
from en_us_normalization.production.verbalize.money import MoneyFst
from en_us_normalization.production.verbalize.ordinal import OrdinalFst
from en_us_normalization.production.verbalize.roman import RomanFst
from en_us_normalization.production.verbalize.telephone import TelephoneFst
from en_us_normalization.production.verbalize.time import TimeFst
from en_us_normalization.production.verbalize.verbatim import VerbatimFst

from learn_to_normalize.grammar_utils.base_fst import BaseFst


class VerbalizeFst(BaseFst):
    """
    Final class that composes all other verbalization grammars.
    Combined rule can process any semiotic class.
    For deployment, this grammar will be compiled and exported to OpenFst Finite State Archive (FAR) File.
    """

    def __init__(self):
        super().__init__(name="verbalize")
        cardinal = CardinalFst()
        decimal = DecimalFst(cardinal=cardinal)
        ordinal = OrdinalFst(cardinal=cardinal)
        fraction = FractionFst(cardinal=cardinal, ordinal=ordinal)
        roman = RomanFst(cardinal=cardinal, ordinal=ordinal)
        address = AddressFst(cardinal=cardinal)
        date = DateFst(cardinal=cardinal, ordinal=ordinal)
        verbatim = VerbatimFst(cardinal=cardinal)
        electronic = ElectronicFst(verbatim=verbatim, cardinal=cardinal)
        measure = MeasureFst(decimal=decimal, fraction=fraction)
        money = MoneyFst(cardinal=cardinal)
        telephone = TelephoneFst(cardinal=cardinal)
        time = TimeFst(cardinal=cardinal)

        # no need for weighting, classification introduces tags,
        # that define semiotic class without ambiguity
        graph = (
            time.fst
            | address.fst
            | date.fst
            | money.fst
            | measure.fst
            | ordinal.fst
            | decimal.fst
            | cardinal.fst
            | telephone.fst
            | electronic.fst
            | fraction.fst
            | roman.fst
            | verbatim.fst
        )
        self.fst = graph
