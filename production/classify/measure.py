"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify measures
"""

import pynini
from en_us_normalization.production.classify.decimal import DecimalFst
from en_us_normalization.production.classify.fraction import FractionFst
from en_us_normalization.production.english_utils import get_data_file_path, singular_to_plural_fst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_space, insert_space


class MeasureFst(BaseFst):
    """
    Finite state transducer for classifying measure, suppletive aware, i.e. 12kg -> 12 kilograms,
    but 1kg -> 1 kilogram. Inside of measure semiotic class there is decimal or fraction
    semiotic subclasses to specify the amount. Measure matches one of those and then measurement units
    from the data file: "measurements.tsv".

    Examples of input strings and transducer outputs:

    - -12kg ->
      measure { decimal { negative: "true" integer_part: "12" } units: "kilograms" }
    - 1kg ->
      measure { decimal { integer_part: "1" } units: "kilogram" }
    - 300,000 km/s ->
      measure { decimal { integer_part: "300000" } units: "kilometers per second" }
    - .5kg ->
      measure { decimal { fractional_part: "5" } units: "kilograms" }

    """

    def __init__(self, decimal: DecimalFst = None, fraction: FractionFst = None):
        """
        constructor of measure fst

        Parameters
        ----------
        decimal: DecimalFst
            fst with decimal numbers to reuse. Created from scratch if not provided.
        fraction: FractionFst
            fst with fractions to reuse as numbers. Created from scratch if not provided.
        """
        super().__init__(name="measure")
        if decimal is None:
            decimal = DecimalFst()
        if fraction is None:
            fraction = FractionFst()

        # expand units, i.e. kg -> kilograms
        units_orig = pynini.string_file(get_data_file_path("measurements.tsv"))
        units_plural_orig = units_orig @ singular_to_plural_fst()
        units = self._add_units_suffix(units_orig, units_orig)
        units_plural = self._add_units_suffix(units_plural_orig, units_orig)

        # decimal with units, i.e. 3.4kg -> decimal { integer_part: "3" fractional_part: "4" } units: "kilograms"
        # special case when singular measures should be used
        one = pynini.accep("1") + pynini.closure(
            pynini.accep(".") + pynini.closure("0", 1)
        )
        decimal_with_singular_unit = one @ decimal.fst + units
        # generic case
        decimal_with_units = decimal.fst + units_plural
        # less probable than special one
        decimal_with_units = pynutil.add_weight(decimal_with_units, 1.1)
        decimal_with_units |= decimal_with_singular_unit

        # fraction with units, for ex. 1/2 kg
        # fraction { numerator: "1" denominator: "2" } units: "kilograms" style_spec_name: "with_explicit_fraction"
        fraction_with_units = (
            fraction.fst
            + units_plural
            + pynutil.insert(' style_spec_name: "with_explicit_fraction"')
        )

        final_graph = decimal_with_units | fraction_with_units
        final_graph = self.add_tokens(final_graph)
        self._single_fst = final_graph.optimize()

    @staticmethod
    def _add_units_suffix(
        prefix_units: pynini.FstLike, suffix_units: pynini.FstLike
    ) -> pynini.FstLike:
        """
        units can have suffix, i.e. plain unit is "m", but unit with a suffix
        is "m/s^2". this helper function takes units transducer and adds optional
        suffix to those
        """
        fix_space = delete_space + insert_space
        suffix_units = pynini.cross("/", "per") + fix_space + suffix_units
        units_tag = delete_space + insert_space + pynutil.insert('units: "')
        units = prefix_units | suffix_units | (prefix_units + fix_space + suffix_units)
        return units_tag + units + pynutil.insert('"')
