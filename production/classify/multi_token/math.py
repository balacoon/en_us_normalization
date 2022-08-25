"""
Copyright Balacoon 2022

tokenize and classify math equations
"""

import pynini
from en_us_normalization.production.classify.cardinal import CardinalFst
from en_us_normalization.production.classify.decimal import DecimalFst
from en_us_normalization.production.classify.fraction import FractionFst
from en_us_normalization.production.classify.measure import MeasureFst
from en_us_normalization.production.classify.money import MoneyFst
from en_us_normalization.production.classify.punctuation_rules import get_punctuation_rules
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_space, insert_space, wrap_token


class MathFst(BaseFst):
    """
    Math is a multi-token where digit-based semiotic classes are separated with operators.
    Some operators hint math straight away: "x", "÷" and "+".
    Some symbols are less likely to be a math operators, so should be treated as such,
    only in cases when the math equation contains more than two elements.
    For example "-" between two digits is rather a range than a minus.
    But if its 3 - 5 + 4, then it's a minus.

    TODO: add brackets and more math symbols (power of, sum, integral, etc)

    Examples of input / output:

    - 3 + 5 ->
      tokens { cardinal { count: "3" } } tokens { name: "plus" } tokens { cardinal { count "5" } }

    """

    def __init__(
        self,
        cardinal: CardinalFst = None,
        decimal: DecimalFst = None,
        money: MoneyFst = None,
        measure: MeasureFst = None,
        fraction: FractionFst = None,
        left_punct: pynini.FstLike = None,
        right_punct: pynini.FstLike = None,
    ):
        """
        constructor of math transducer. All the parameters are digit-based transducers which
        can be connected with math operators.

        Parameters
        ----------
        cardinal: CardinalFst
            a cardinal to reuse
        decimal: DecimalFst
            a decimal to reuse
        money: MoneyFst
            money to reuse
        measure: MeasureFst
            a measure to reuse
        fraction: FractionFst
            a fraction to reuse
        left_punct: pynini.FstLike
            punctuation to the left of multi-token
        right_punct: pynini.FstLike
            punctuation to the right of multi-token
        """
        super().__init__(name="math")

        # initialize transducers if those are not provided
        # may be needed in testing.
        if cardinal is None:
            cardinal = CardinalFst()
        if decimal is None:
            decimal = DecimalFst(cardinal=cardinal)
        if money is None:
            money = MoneyFst(decimal=decimal)
        if measure is None:
            measure = MeasureFst(decimal=decimal, fraction=fraction)
        if fraction is None:
            fraction = FractionFst(cardinal=cardinal)
        if left_punct is None and right_punct is None:
            left_punct, right_punct = get_punctuation_rules()

        fix_space = (
            insert_space + delete_space
        )  # ensures there is exactly one space even if there were none
        digit_semiotic = (
            pynutil.add_weight(cardinal.single_fst, 9.0)
            | pynutil.add_weight(decimal.fst, 10.0)
            | pynutil.add_weight(money.fst, 1.1)
            | pynutil.add_weight(measure.fst, 1.1)
            | pynutil.add_weight(fraction.fst, 10.0)
        )

        left_token = wrap_token(left_punct + digit_semiotic)
        right_token = wrap_token(digit_semiotic + right_punct)

        math_operators = [
            pynini.cross("x", 'name: "by"'),
            pynini.cross("÷", 'name: "divided by"'),
            pynini.cross("+", 'name: "plus"'),
        ]
        math_operators = [wrap_token(x) for x in math_operators]
        math_operators = pynini.union(*math_operators)

        # math equation from 2 elements
        simple_graph = left_token + fix_space + math_operators + fix_space + right_token

        # add minus to math operators, but it has to be surrounded with spaces, otherwise its likely dash
        math_operators |= wrap_token(pynini.cross(" - ", 'name: "minus"'))
        # math equations from 3 and more elements
        repeated_token = pynini.closure(
            fix_space + math_operators + fix_space + wrap_token(digit_semiotic), 1
        )
        complex_graph = (
            left_token
            + repeated_token
            + fix_space
            + math_operators
            + fix_space
            + right_token
        )

        graph = simple_graph | complex_graph
        self._multi_fst = graph.optimize()
