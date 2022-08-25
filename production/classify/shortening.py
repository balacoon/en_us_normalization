"""
Copyright 2022 Balacoon
Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
Copyright 2015 and onwards Google, Inc.

expand shortenings
"""

import pynini
from en_us_normalization.production.english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_mapping
from learn_to_normalize.grammar_utils.shortcuts import LOWER, TO_LOWER


class ShorteningFst(BaseFst):
    """
    Finite state transducer for discovering shortenings, such as Mrs. or prof.
    All shortenings and their mappings are stored in:

    - shortenings/case_agnostic.tsv - shortenings that should be expanded for any case
    - shortenings/cased.tsv - shortenings that require precise writing as in the data file to be expanded

    Shortenings are expanded immediately, so no need to separate verbalization
    or dedicated semiotic class.

    Examples of input/output strings:

    - mrs. ->
      name: "misses"
    """

    def __init__(self):
        super().__init__(name="shortening")

        # some custom shortenings that require context
        # 1. street vs saint. partially resolved when full address is provided.
        delete_optional_dot = pynini.closure(pynutil.delete("."), 0, 1)
        st = (pynini.accep("st") | pynini.accep("ST") | pynini.accep("St")) + delete_optional_dot
        st_street = pynini.cross(st, "street")
        graph = TO_LOWER + pynini.closure(LOWER, 1) + pynini.accep(" ") + st_street
        st_saint = pynini.cross(st, "saint")
        graph |= st_saint + pynini.accep(" ") + TO_LOWER + pynini.closure(LOWER, 1)

        graph |= load_mapping(
            get_data_file_path("shortenings", "case_agnostic.tsv"),
            key_case_agnostic=True,
            key_with_dot=True,
        )
        graph |= load_mapping(
            get_data_file_path("shortenings", "cased.tsv"), key_case_agnostic=False
        )
        graph = pynutil.insert('name: "') + graph + pynutil.insert('"')
        self._single_fst = graph.optimize()
