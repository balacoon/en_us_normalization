"""
Copyright Balacoon 2022

verbalizes addresses
"""

import pynini
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.shortcuts import (
    LOWER,
    SPACE,
    TO_LOWER,
    UPPER,
    insert_space,
)


class AddressFst(BaseFst):
    """
    Finite state transducer for verbalizing address.
    All the heavy lifting (i.e. expanding shortenings) happens during classification.
    Verbalization of addresses simply includes bringing everything to lower case
    and removing fields ids. Set of possible fields in address is rather big,
    check configs/verbalizer_serialization_spec.ascii_proto for reference.
    Numbers in address are expanded reusing cardinal verbalization transducer.

    Examples of input/output strings:

    - address|house:1|street_name:Nice|street_type:street| -> one nice street

    """

    def __init__(self, cardinal: CardinalFst = None):
        """
        constructor of address verbalizer

        Parameters
        ----------
        cardinal: CardinalFst
            reusing cardinal verbalizer to expand numbers
        """
        super().__init__(name="address")
        if cardinal is None:
            cardinal = CardinalFst()

        # house number is mandatory (TODO: maybe shouldn't be, to find St.)
        house = cardinal.get_digit_pairs_fst()
        house = pynutil.delete("house:") + house + pynutil.delete("|")

        # optional directional, it can occur before/after street
        # possible values are in data/address/directional.tsv
        directional = pynini.closure(LOWER | SPACE, 1)
        pre_directional = (
            pynutil.delete("pre_directional:") + directional + pynutil.delete("|")
        )
        optional_pre_directional = pynini.closure(insert_space + pre_directional, 0, 1)
        post_directional = (
            pynutil.delete("post_directional:") + directional + pynutil.delete("|")
        )
        optional_post_directional = pynini.closure(
            insert_space + post_directional, 0, 1
        )

        # street name and type are mandatory
        # street name can have multiple words
        street_name = pynini.closure(LOWER | TO_LOWER | pynini.accep("-") | SPACE, 1)
        street_name = pynutil.delete("street_name:") + street_name + pynutil.delete("|")
        # street types come from data/address/street_type.tsv
        street_type = pynini.closure(LOWER, 1)
        street_type = pynutil.delete("street_type:") + street_type + pynutil.delete("|")
        street = insert_space + street_name + insert_space + street_type

        # optional suite (type and number)
        # suite type comes from data/address/suite_type.tsv or just "PO box"
        suite_type = pynini.closure(LOWER | SPACE, 1)
        suite_type = pynutil.delete("suite_type:") + suite_type + pynutil.delete("|")
        # suite number is just a number
        suite_number = cardinal.get_cardinal_expanding_fst()
        suite_number = (
            pynutil.delete("suite_number:") + suite_number + pynutil.delete("|")
        )
        # suite can be just type (PO Box), just number or type + number
        suite = suite_number | suite_type | (suite_type + insert_space + suite_number)
        optional_suite = pynini.closure(insert_space + suite, 0, 1)

        # optional town - just letters
        town = pynini.closure(LOWER | TO_LOWER | SPACE, 1)
        town = pynutil.delete("town:") + town + pynutil.delete("|")
        optional_town = pynini.closure(insert_space + town, 0, 1)

        # optional state
        # comes from data/address/state.tsv or accepts those from data file
        state = pynini.closure(LOWER | TO_LOWER | SPACE, 1)
        state = pynutil.delete("state:") + state + pynutil.delete("|")
        optional_state = pynini.closure(insert_space + state, 0, 1)

        # optional zip code
        # zip is either american with all digits or british with mix of digits and uppercase letters.
        # in either case numbers and letters are read character by character.
        # make it a bit more expensive to insert spaces to keep characters together
        letters = pynutil.add_weight(insert_space, 1.1) + pynini.closure(UPPER, 1)
        digits = insert_space + cardinal.get_digit_by_digit_fst()
        zip = pynini.closure(letters | digits, 1)
        zip = pynutil.delete("zip:") + zip + pynutil.delete("|")
        # letters and digits already insert space in front of fst
        optional_zip = pynini.closure(zip, 0, 1)

        address = (
            house
            + optional_pre_directional
            + street
            + optional_post_directional
            + optional_suite
            + optional_town
            + optional_state
            + optional_zip
        )
        self.fst = self.delete_tokens(address).optimize()
