"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

Verbalizes time
"""

import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import DIGIT, NOT_BAR, insert_space


class TimeFst(BaseFst):
    """
    Finite state transducer for verbalizing time. Time tokenizer already classifies
    time zone and suffix and converts them for spelling. Time verbalizer's
    job is to remove tags and expand numbers for hours and minutes.
    There are couple of exceptions to take care of:

    - hours:00|miunutes:10| - should be twelve ten, i.e. "00" or "0" hours turned into twelve
    - hours:07|minutes:10| - should be 7, i.e. trailing zero is deleted
    - hours:12| - for hours without minutes and suffix, "o'clock is appended"
    - hours:12|minutes:00| - if there is no suffix, "00" minutes are replaced with "o'clock"

    Examples if input/output strings:

    - time|hours:12|minutes:30|suffix:AM|zone:EST| -> twelve thirty AM EST
    - time|hours:12| -> twelve o'clock

    """

    def __init__(self, cardinal: CardinalFst = None):
        """
        constructor of time verbalizer

        Parameters
        ----------
        cardinal: CardinalFst
            cardinal to reuse to expand hours and minutes into spoken form
        """
        super().__init__(name="time")
        if cardinal is None:
            cardinal = CardinalFst()

        # hours is mandatory to have, reuse cardinal to expand it
        # if there is trailing 0, remove it
        hours = pynutil.add_weight(DIGIT + DIGIT, 1.2) | pynutil.add_weight(
            pynutil.delete("0") + DIGIT, 1.1
        )
        hours = hours @ cardinal.get_cardinal_expanding_fst()
        # if hours are zero - use twelve
        hours |= pynini.cross("0", "twelve")
        hours |= pynini.cross("00", "twelve")
        hours = pynutil.delete("hours:") + hours + pynutil.delete("|")

        # minutes are optional, to expand - use digit pairs expansion
        minutes = cardinal.get_digit_pairs_fst()
        minutes = pynutil.delete("minutes:") + minutes + pynutil.delete("|")
        optional_minutes = pynini.closure(insert_space + minutes, 0, 1)

        # for suffix - just remove field, it is already normalized to be spelled
        suffix = (
            pynutil.delete("suffix:") + pynini.closure(NOT_BAR, 1) + pynutil.delete("|")
        )
        optional_suffix = pynini.closure(insert_space + suffix, 0, 1)

        # same as for suffix
        zone = (
            pynutil.delete("zone:") + pynini.closure(NOT_BAR, 1) + pynutil.delete("|")
        )
        optional_zone = pynini.closure(insert_space + zone, 0, 1)

        # there is hours and either minutes or suffix
        hours_minutes_suffix = pynutil.add_weight(
            hours + optional_minutes + optional_suffix, 1.1
        )
        # if there are no minutes and no suffix, add "o'clock"
        hours_minutes_suffix |= hours + pynutil.insert(" o'clock")
        # if there is no suffix and minutes are zeros add "o'clock"
        hours_minutes_suffix |= hours + pynini.cross("minutes:00|", " o'clock")
        graph = hours_minutes_suffix + optional_zone
        self._single_fst = self.delete_tokens(graph).optimize()
