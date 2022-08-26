"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify money
"""

import pynini
from en_us_normalization.production.classify.decimal import DecimalFst
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_union
from learn_to_normalize.grammar_utils.shortcuts import insert_space


class MoneyFst(BaseFst):
    """
    Finite state transducer for classifying money, suppletive aware.
    Reuses decimal transducer prepending or appending currency.
    Currencies are listed in "currency/major.tsv" data file.
    Most of the work is done in verbalizer to assign major/minor currencies.

    Examples of input and tagged money strings:

    - $12.05 ->
      money { currency: "$" decimal { integer_part: "12" fractional_part: "05" } }
    - $1 ->
      money { currency: "$" decimal { integer_part: "1" } }
    - 13.99£ ->
      money { decimal { integer_part: "13" fractional_part: "99" } currency: "£" }

    """

    def __init__(self, decimal: DecimalFst = None):
        """
        constructor of money tagging transuducer

        Parameters
        ----------
        decimal: DecimalFst
            decimal transducer to reuse for amount.
            if not provided, created from scratch.
        """
        super().__init__(name="money")
        if decimal is None:
            decimal = DecimalFst()

        currency = load_union(get_data_file_path("currency", "major.tsv"))
        currency = pynutil.insert('currency: "') + currency + pynutil.insert('"')

        # when decimal doesnt have a quantity, just integer/fractional part
        decimal_wo_quantity = (
            pynutil.insert("decimal { ")
            + decimal.get_basic_decimal_fst()
            + pynutil.insert(" }")
        )
        currency_before_amount = currency + insert_space + decimal_wo_quantity
        currency_after_amount = decimal_wo_quantity + insert_space + currency
        money_wo_quantity = currency_before_amount | currency_after_amount

        # when decimal has a quantity has to insert specification style name,
        # because it is expanded differently.
        # enlarge set of supported quantities with lower-case "m"
        extra_quantity = pynini.cross("m", "million")
        decimal_with_quantity = (
            pynutil.insert("decimal { ")
            + decimal.add_quantity(decimal.get_basic_decimal_fst(), extra_quantity=extra_quantity)
            + pynutil.insert(" }")
        )
        specification_name = pynutil.insert(' style_spec_name: "with_quantity"')
        currency_before_amount = currency + insert_space + decimal_with_quantity
        currency_after_amount = decimal_with_quantity + insert_space + currency
        money_with_quantity = currency_before_amount | currency_after_amount
        money_with_quantity += specification_name

        graph = money_wo_quantity | money_with_quantity
        graph = self.add_tokens(graph)
        self._single_fst = graph.optimize()
        self.connect_to_self(connector_in="-", connector_out="to")
