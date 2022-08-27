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
        hours = (
            pynutil.add_weight(DIGIT + DIGIT, 1.2)
            | pynutil.add_weight(pynutil.delete("0") + DIGIT, 1.1)
            | DIGIT
        )
        hours = hours @ cardinal.get_cardinal_expanding_fst()
        # if hours are zero - use twelve
        hours |= pynini.cross("0", "twelve")
        hours |= pynini.cross("00", "twelve")
        hours = pynutil.delete("hours:") + hours + pynutil.delete("|")

        # minutes are optional, to expand - use digit pairs expansion
        minutes_wo_tag = pynutil.add_weight(cardinal.get_digit_pairs_fst(), 1.1)
        minutes_wo_tag |= (pynutil.insert("o") + insert_space + DIGIT @ cardinal.get_digit_by_digit_fst())
        minutes = pynutil.delete("minutes:") + minutes_wo_tag + pynutil.delete("|")
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

        # accurate time option
        accurate_time = self._get_accurate_time_fst(cardinal) + optional_suffix
        hours_minutes_suffix |= accurate_time

        graph = hours_minutes_suffix + optional_zone
        self._single_fst = self.delete_tokens(graph).optimize()

    @staticmethod
    def _get_accurate_time_fst(cardinal: CardinalFst) -> pynini.FstLike:
        """
        helper function that produces fst for accurate time - one with seconds/milliseconds.
        Format is: hh:mm:ss.mmm
        """
        two_digits = pynini.closure(DIGIT, 1, 2) @ cardinal.get_cardinal_expanding_fst()

        # hours
        hours = pynutil.delete("hours:") + two_digits + pynutil.delete("|")
        hours = (
            pynutil.add_weight((hours + pynutil.insert(" hours ")), 1.1)
            | pynini.cross("hours:1|", "one hour ")
        )

        # similar minutes, but allow it to be absent
        minutes = pynutil.delete("minutes:") + two_digits + pynutil.delete("|")
        minutes = (
            pynutil.add_weight((minutes + pynutil.insert(" minutes")), 1.1)
            | pynini.cross("minutes:1|", "one minute")
            | pynutil.insert("zero minutes")
        )

        # special case for singular
        singular_seconds = pynini.cross("seconds:1|", "one second")
        # seconds expand the same way as minutes. seconds are expanded with suffix
        seconds = pynutil.delete("seconds:") + two_digits + pynini.cross("|", " seconds")
        seconds = singular_seconds | pynutil.add_weight(seconds, 1.1)

        # special case for singular
        singular_milliseconds = pynini.cross("milliseconds:1|", "one millisecond")
        # milliseconds are expanded as cardinal with suffix
        milliseconds = pynini.closure(DIGIT, 1, 3) @ cardinal.get_cardinal_expanding_fst()
        milliseconds = pynutil.delete("milliseconds:") + milliseconds + pynini.cross("|", " milliseconds")
        milliseconds = singular_milliseconds | pynutil.add_weight(milliseconds, 1.1)

        hh_mm = hours + minutes
        hh_mm_ss = hh_mm + pynutil.insert(" and ") + seconds
        hh_mm_ms = hh_mm + pynutil.insert(" and ") + milliseconds
        hh_mm_ss_ms = hh_mm + insert_space + seconds + pynutil.insert(" and ") + milliseconds
        accurate_time = (hh_mm_ss | hh_mm_ms | hh_mm_ss_ms)
        return accurate_time
