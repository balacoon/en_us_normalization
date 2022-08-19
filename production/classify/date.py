"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

tokenize and classify dates
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import (
    CHAR,
    DIGIT,
    TO_LOWER,
    TO_UPPER,
    delete_extra_space,
    delete_space,
    insert_space,
)


class DateFst(BaseFst):
    """
    Finite state transducer for classifying dates. Dates can be written in a lot of different ways:

    - `conventional date` in a form of 2012/12/12. Multiple separators are possible: "/", "-", "."
      There might be a confusion which one is which, especially if
      year is written with two digits. There are few things that can help with proper identification:
      months are in range 01-12, days are in range 1-31. In case of ambiguity proceed with MDY format,
      but this should be locale-dependent.
    - `written date` in a form of jan. 5, 2012. Here the order may wary. Depending on the order,
      specific style should be used (see configs/verbalizer_serialization_spec.ascii_proto).
      Few tricks for this date format: 1) day can be ordinal, i.e. have suffix "th", "st", etc.;
      2) year can have era attached i.e. "960 BC".
      In this format, some fields are optional: i.e. year may be missing, day can be missing.
    - `stand-alone years` - very tricky to detect, because it requires context to understand that the number
      is a year. Fortunately transducing year as a cardinal wouldn't be a huge deal.
      however for modern years, such as 1995 or 2012, its better to tag those as years and verbalize
      in blocks of 2 digits.
    - `decades` - when whole decade is meant, which is marked with "s" at the end. year has to end with "0".
      optionally first two digits of the year are ommitted and replaced with apostroph. Possible examples:
      1960s or '60s. Era field is reused to mark decades, not to introduce separate field

    Examples of the date normalization:

    - jan. 5, 2012 ->
      date { month: "january" day: "5" year: "2012" }
    - jan. 5 ->
      date { month: "january" day: "5" }
    - jan. 5th ->
      date { month: "january" day: "5" }
    - 5 january 2012 ->
      date { day: "5" month: "january" year: "2012" style_spec_name: "dmy" }
    - 5 january 960 B.C. ->
      date { day: "5" month: "january" year: "960" era: "BC" style_spec_name: "dmy" }
    - 2012-01-05 ->
      date { year: "2012" month: "january" day: "5" style_spec_name: "dmy" }
    - 2012.01.05 ->
      date { year: "2012" month: "january" day: "5" style_spec_name: "dmy" }
    - 2012/01/05 ->
      date { year: "2012" month: "january" day: "5" style_spec_name: "dmy" }
    - 12/01/05 ->
      date { year: "12" month: "january" day: "5" style_spec_name: "dmy" }
    - 2012 ->
      date { year: "2012" }
    - 1960s ->
      date { year: "1960" era: "s" }
    - '60s ->
      date { year: "60" era: "s" }

    """
    def __init__(self):
        super().__init__(name="date")

        # days expressed in numbers
        days = self._get_days_fst()

        # 4-digit year
        modern_year = self._get_modern_year_fst()

        # conventional date: 2012/12/12
        conventional_date = self._get_conventional_date_fst(days, modern_year)

        # written date: 5 jan. 2012
        written_date = self._get_written_date_fst(days)

        # Stand-alone years, i.e. 2001
        four_digit_year = pynutil.insert('year: "') + modern_year + pynutil.insert('"')
        standalone_year = pynutil.add_weight(four_digit_year, 1.1)

        # decades, i.e. 1950s or '60s
        delete_apostroph = pynini.closure(pynutil.delete("'"), 0, 1)
        ies = pynutil.insert('" era: "') + delete_apostroph + "s" + pynutil.insert('"')
        decade = (
            pynutil.insert('year: "')
            + pynini.union("1", "2")
            + DIGIT
            + DIGIT
            + "0"
            + ies
        )
        decade_short = pynutil.insert('year: "') + delete_apostroph + DIGIT + "0" + ies
        decade |= decade_short

        final_graph = conventional_date | written_date | standalone_year | decade
        final_graph = self.add_tokens(final_graph)
        self.fst = final_graph.optimize()

    @staticmethod
    def _get_days_fst() -> pynini.FstLike:
        """
        reusable day fst, written as number, i.e. 1-31.
        One-digit days can be pre-pended with "0"
        """
        # days in number form
        # single digit day (1-9), i.e. 1, 2, ... 9.
        days = DIGIT - "0"
        # two digit day (1-9), i.e. 01, 02, ... 09.
        days |= pynutil.delete("0") + (DIGIT - "0")
        # day 10-29, i.e. 10, 11, ... 29
        days |= pynini.union("1", "2") + DIGIT
        # days 30, 31
        days |= pynini.union("30", "31")
        return days

    @staticmethod
    def _get_modern_year_fst() -> pynini.FstLike:
        """
        reusable modern year fst.
        modern year - means has 4 digits, starts with "1" or "20"
        """
        modern_year_prefix = pynini.accep("1") + DIGIT | pynini.accep("20")
        modern_year = modern_year_prefix + DIGIT + DIGIT
        return modern_year

    @staticmethod
    def _get_conventional_date_fst(
        days: pynini.FstLike, modern_year: pynini.FstLike
    ) -> pynini.FstLike:
        """
        conventional data format, such as 2012/12/12.
        days are reused in other date transducers
        """
        two_digit_year = DIGIT + DIGIT
        year = (
            pynutil.insert('year: "')
            + (modern_year | two_digit_year)
            + pynutil.insert('"')
        )
        # months in number form
        month = pynini.string_file(
            get_data_file_path("months", "numbers.tsv")
        ).optimize()
        month = pynutil.insert('month: "') + month + pynutil.insert('"')
        # wrap days into a tag
        days = pynutil.insert('day: "') + days + pynutil.insert('"')
        # possible separators
        delete_sep = pynutil.delete(pynini.union("-", "/", "."))
        conventional_date_dmy = (
            days
            + delete_sep
            + insert_space
            + month
            + delete_sep
            + insert_space
            + year
            + pynutil.insert(' style_spec_name: "dmy"')
        )
        # dmy is less probable than mdy for en_us
        conventional_date_dmy = pynutil.add_weight(conventional_date_dmy, 1.1)
        conventional_date_mdy = (
            month + delete_sep + insert_space + days + delete_sep + insert_space + year
        )
        conventional_date_ymd = (
            year
            + delete_sep
            + insert_space
            + month
            + delete_sep
            + insert_space
            + days
            + pynutil.insert(' style_spec_name: "dmy"')
        )
        conventional_date_ymd = pynutil.add_weight(conventional_date_ymd, 1.1)
        conventional_date = (
            conventional_date_dmy | conventional_date_mdy | conventional_date_ymd
        )
        return conventional_date

    @staticmethod
    def _get_written_date_fst(days: pynini.FstLike) -> pynini.FstLike:
        # months in written form (full or abbreviation)
        month = pynini.string_file(get_data_file_path("months", "names.tsv")).optimize()
        # allows "january" (from names.tsv) and "January"
        month |= (TO_LOWER + pynini.closure(CHAR)) @ month
        month_abbr = pynini.string_file(
            get_data_file_path("months", "abbr.tsv")
        ).optimize()
        month_abbr |= (TO_LOWER + pynini.closure(CHAR)) @ month_abbr
        month |= month_abbr + pynini.closure(pynutil.delete("."), 0, 1)
        month = pynutil.insert('month: "') + month + pynutil.insert('"')
        # written form years, any number up to 4 digits long
        year = (DIGIT - "0") + pynini.closure(DIGIT, 0, 3)
        year = pynutil.insert('year: "') + year + pynutil.insert('"')
        # era - bc, bce, ad, ce. could be capital letters, could be separated with dots
        delete_optinal_dot = pynini.closure(pynutil.delete("."), 0, 1)
        bc_era = (
            delete_space
            + "B"
            + delete_optinal_dot
            + "C"
            + delete_optinal_dot
            + pynini.closure("E", 0, 1)
            + delete_optinal_dot
        )
        bc_era |= (
            delete_space + pynini.closure(TO_UPPER + delete_optinal_dot, 2, 3) @ bc_era
        )
        ad_era = delete_space + "A" + delete_optinal_dot + "D" + delete_optinal_dot
        ad_era |= (
            delete_space + pynini.closure(TO_UPPER + delete_optinal_dot, 2, 2) @ ad_era
        )
        ce_era = delete_space + "C" + delete_optinal_dot + "E" + delete_optinal_dot
        ce_era |= (
            delete_space + pynini.closure(TO_UPPER + delete_optinal_dot, 2, 2) @ ce_era
        )
        ce_era |= ad_era
        era = bc_era | ce_era
        era = pynutil.insert(' era: "') + era + pynutil.insert('"')
        year_and_era = year + pynini.closure(era, 0, 1)
        year_and_era = (
            pynini.closure(pynutil.delete(","), 0, 1)
            + delete_extra_space
            + year_and_era
        )
        # written form of days
        delete_ordinal_suffix = pynini.closure(
            pynutil.delete(pynini.union("st", "nd", "rd", "th")), 0, 1
        )
        days = delete_space + days + delete_ordinal_suffix
        days = pynutil.insert('day: "') + days + pynutil.insert('"')
        # date in a written form
        # dmy with optional year
        optional_days = pynini.closure(days, 0, 1)
        optional_year = pynini.closure(year_and_era, 0, 1)
        written_date_dmy = (
            optional_days + delete_space + insert_space + month + optional_year
        )
        written_date_dmy = pynutil.add_weight(
            written_date_dmy + pynutil.insert(' style_spec_name: "dmy"'), 1.1
        )
        # mdy with optional day and year. days has more probability than year
        optional_days_with_space = pynini.closure(insert_space + days, 0, 1)
        optional_year = pynini.closure(pynutil.add_weight(year_and_era, 1.1), 0, 1)
        written_date_mdy = month + optional_days_with_space + optional_year
        written_date = written_date_dmy | written_date_mdy
        return written_date
