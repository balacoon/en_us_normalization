"""
Copyright Balacoon 2022

tokenize and classify ranges
"""

import pynini
from en_us_normalization.production.classify.cardinal import CardinalFst
from en_us_normalization.production.classify.date import DateFst
from en_us_normalization.production.classify.decimal import DecimalFst
from en_us_normalization.production.classify.fraction import FractionFst
from en_us_normalization.production.classify.measure import MeasureFst
from en_us_normalization.production.classify.money import MoneyFst
from en_us_normalization.production.classify.punctuation_rules import get_punctuation_rules
from en_us_normalization.production.classify.roman import RomanFst
from en_us_normalization.production.classify.time import TimeFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import delete_space, insert_space, wrap_token


class RangeFst(BaseFst):
    """
    Range is a multi-token, where two digit-based semiotic classes are connected with "-",
    which is pronounced as "to". Range can be between dates, times, cardinals, measures, fractions, decimals, etc.
    Range is more probable then "minus". Range consists of only 2 semiotic classes and connector.
    It is similar to ScoreFst, but number of semiotic classes between which range is possible is bigger.

    Examples of input / output:

    - 1 - 2 ->
      tokens { cardinal { count: "1" } } tokens { name: "to" } tokens { cardinal { count "2" } }

    """

    def __init__(
        self,
        cardinal: CardinalFst = None,
        decimal: DecimalFst = None,
        money: MoneyFst = None,
        measure: MeasureFst = None,
        fraction: FractionFst = None,
        date: DateFst = None,
        time: TimeFst = None,
        roman: RomanFst = None,
        left_punct: pynini.FstLike = None,
        right_punct: pynini.FstLike = None,
    ):
        """
        constructor of range transducer. All the parameters are digit-based transducers which
        can be connected with a dash to signalize a range

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
        date: DateFst
            a date to reuse
        time: TimeFst
            time to reuse
        roman: RomanFst
            roman numbers to reuse
        left_punct: pynini.FstLike
            punctuation to the left of multi-token
        right_punct: pynini.FstLike
            punctuation to the right of multi-token
        """
        super().__init__(name="range")

        # initialize transducers if those are not provided
        # may be needed in testing.
        if cardinal is None:
            cardinal = CardinalFst()
        if date is None:
            date = DateFst()
        if time is None:
            time = TimeFst()
        if decimal is None:
            decimal = DecimalFst(cardinal=cardinal)
        if fraction is None:
            fraction = FractionFst(cardinal=cardinal)
        if money is None:
            money = MoneyFst(decimal=decimal)
        if roman is None:
            roman = RomanFst(cardinal=cardinal)
        if measure is None:
            measure = MeasureFst(decimal=decimal, fraction=fraction)
        if left_punct is None and right_punct is None:
            left_punct, right_punct = get_punctuation_rules()

        fix_space = insert_space + delete_space
        digit_semiotic = (
            pynutil.add_weight(cardinal.fst, 9.0)
            | pynutil.add_weight(decimal.fst, 10.0)
            | pynutil.add_weight(money.fst, 1.1)
            | pynutil.add_weight(measure.fst, 1.1)
            | pynutil.add_weight(fraction.fst, 10.0)
            | pynutil.add_weight(date.fst, 1.01)
            | pynutil.add_weight(time.fst, 1.1)
            | pynutil.add_weight(roman.fst, 1.09)
        )
        graph = (
            wrap_token(left_punct + digit_semiotic)
            + fix_space
            + wrap_token(pynini.cross("-", 'name: "to"'))
            + fix_space
            + wrap_token(digit_semiotic + right_punct)
        )
        self.fst = graph.optimize()
