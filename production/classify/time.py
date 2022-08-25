"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify time
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_union
from learn_to_normalize.grammar_utils.shortcuts import (
    ALPHA,
    DIGIT,
    SIGMA,
    SPACE,
    TO_UPPER,
    UPPER,
    delete_space,
    insert_space,
)


class TimeFst(BaseFst):
    """
    Finite state transducer for classifying time.
    Slots to fill when time is parsed:

    - hours - 1-2 digit number
    - minutes - 1-2 digit number (optional)
    - suffix - abbreviation such as AM or PM (optional)
    - time zone - abbreviation at the end such as EST (optional)

    Hours and minutes can be separated with ":" or ".".
    At least one successor should (minutes, suffix or time zone) should help to classify
    digits as hours.

    Examples of input/output strings:

    - 12:30 a.m. est -> time { hours: "12" minutes: "30" suffix: "AM" zone: "EST" }
    - 2.30 a.m. -> time { hours: "2" minutes: "30" suffix: "AM" }
    - 02.30 a.m. -> time { hours: "2" minutes: "30" suffix: "AM" }
    - 2.00 a.m. -> time { hours: "2" suffix: "AM" }
    - 2 a.m. -> time { hours: "2" suffix: "AM" }
    - 02:00 -> time { hours: "2" }
    - 2:00 -> time { hours: "2" }
    """

    def __init__(self):
        super().__init__(name="time")

        suffix = self.load_shortenings("suffix.tsv")
        suffix = pynutil.insert('suffix: "') + suffix + pynutil.insert('"')
        suffix_optional = pynini.closure(delete_space + insert_space + suffix, 0, 1)

        time_zone = self.load_shortenings("zone.tsv")
        time_zone = pynutil.insert('zone: "') + time_zone + pynutil.insert('"')
        time_zone_optional = pynini.closure(
            delete_space + insert_space + time_zone, 0, 1
        )

        hours = [str(x) for x in range(0, 24)]
        delete_leading_zero = DIGIT + DIGIT
        delete_leading_zero |= pynini.closure(pynutil.delete("0"), 0, 1) + DIGIT
        hours = delete_leading_zero @ pynini.union(*hours)
        hours = pynutil.insert('hours: "') + hours + pynutil.insert('"')

        minutes_single = [str(x) for x in range(1, 10)]
        minutes_double = [str(x) for x in range(10, 60)]
        minutes_single = pynini.union(*minutes_single)
        minutes_double = pynini.union(*minutes_double)
        minutes = pynini.cross("0", "O") + insert_space + minutes_single
        minutes |= minutes_double
        minutes = pynutil.insert('minutes: "') + minutes + pynutil.insert('"')

        # 2:30 pm, 02:30, 2:00
        graph_hm = (
            hours
            + (pynutil.delete(":") | pynutil.delete("."))
            + (pynutil.delete("00") | insert_space + minutes)
            + suffix_optional
            + time_zone_optional
        )

        # 2 pm est
        graph_h = hours + delete_space + insert_space + suffix + time_zone_optional
        graph_h |= hours + delete_space + insert_space + time_zone

        final_graph = (graph_hm | graph_h).optimize()
        final_graph = self.add_tokens(final_graph)
        self._single_fst = final_graph.optimize()
        self.connect_to_self(connector_in="-", connector_out="to")

    @staticmethod
    def load_shortenings(name: str) -> pynini.FstLike:
        """
        helper function to load time shortenings - suffixes and time zones.
        produces transducer that allows lower case, upper case,
        dots-between-letters shortenings from the list
        """
        allowed_shortenings = load_union(get_data_file_path("time", name))

        # compose permissive shortening transducer
        symbol = ALPHA | pynini.accep(".") | SPACE
        # 9 stands for 3-char shortening with dots and spaces after each letter
        shortening = pynini.closure(symbol, 2, 9)
        # remove dots and spaces
        shortening = shortening @ pynini.cdrewrite(pynini.cross(".", ""), "", "", SIGMA)
        shortening = shortening @ pynini.cdrewrite(
            pynini.cross(SPACE, ""), "", "", SIGMA
        )
        # turn to upper case since those abbreviations should be spelled
        to_upper = pynini.closure(TO_UPPER | UPPER)
        shortening = shortening @ to_upper

        # allow only shortenings from file
        return shortening @ allowed_shortenings
