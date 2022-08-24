"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes measures
"""

import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from en_us_normalization.production.verbalize.decimal import DecimalFst
from en_us_normalization.production.verbalize.fraction import FractionFst
from en_us_normalization.production.verbalize.ordinal import OrdinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import NOT_BAR, insert_space


class MeasureFst(BaseFst):
    """
    Finite state transducer for verbalizing measures. Measures are a combination of
    decimal/fraction number and a measurement units. Measurement units are already
    normalized during classification. So in verbalization of measurements we reuse
    verbalization of decimal/fraction and just drop fields for measurement units.

    Examples of input/output strings:

    - measure|negative:1|integer_part:12|units:kilograms| -> minus twelve kilograms
    - measure|integer_part:12|fractional_part:5|units:kilograms| -> twelve point five kilograms
    - measure|integer_part:23|numerator:4|denominator:5|units:miles per hour| ->
      twenty three and four fifths miles per hour

    """

    def __init__(self, decimal: DecimalFst = None, fraction: FractionFst = None):
        super().__init__(name="measure")
        cardinal = None
        if decimal is None:
            cardinal = CardinalFst()
            decimal = DecimalFst(cardinal=cardinal)
        if fraction is None:
            if cardinal is None:
                cardinal = CardinalFst()
            ordinal = OrdinalFst(cardinal=cardinal)
            fraction = FractionFst(cardinal=cardinal, ordinal=ordinal)

        # depending on the style
        numbers = decimal.get_graph() | fraction.get_graph()
        units = (
            insert_space
            + pynutil.delete("units:")
            + pynini.closure(NOT_BAR, 1)
            + pynutil.delete("|")
        )
        graph = numbers + units
        self.fst = self.delete_tokens(graph).optimize()
