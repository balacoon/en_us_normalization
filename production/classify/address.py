"""
Copyright Balacoon 2022

tokenizes and classifies addresses
"""

import pynini
from english_utils import get_data_file_path
from pynini.lib import pynutil

from learn_to_normalize.grammar_utils.base_fst import BaseFst
from learn_to_normalize.grammar_utils.data_loader import load_mapping
from learn_to_normalize.grammar_utils.shortcuts import ALPHA, DIGIT, LOWER, TO_LOWER, TO_UPPER, UPPER


class AddressFst(BaseFst):
    """
    Finite state transducer for classifying address.
    Address consists of multiple slots, most of which are optional.
    Those slots are:

    1. house number - mandatory
    2. street, consisting of name, type (road, street, square, etc),
       pre- or post- directional (N for north) - mandatory
    3. suite - apartment or house number, consists of type and number (for ex. Apt #23) - optional
    4. town - possibly multi-word town (for ex. San-Francisco) - optional
    5. state - usually abbreviated state (for ex. CA) - optional
    6. zip-code - 5-digit number with optional dash-separated 4-digits extension (for ex. 45149-3214).
       Another option for zip-code is british format zip code, such as "SW1W 0NY". That one consitst of
       outcode and incode separated by space - optional

    Examples of addresses and their parsing:

    - 1599 Curabitur Rd. Bandera South Dakota 45149 ->
      address { house: "1599" street_name: "Curabitur" street_type: "road"
      town: "Bandera" state: "South Dakota" zip: "45149"}
    - 123 N Malanyuka St. SE, Apt #23 San-Francisco CA 45149-3214 ->
      address { house: "123" pre_directional: "north"
      street_name: "Malanyuka" street_type: "street"
      post_directional: "south east"
      suite_type: "apartment" suite_number: "23"
      town: "San Francisco" state: "california" zip: "451493214"}
    """

    def __init__(self):
        super().__init__(name="address")

        # house number - just digits with optional dash, for ex. 123, 928-3313
        house_number = pynini.closure(DIGIT | pynini.cross("-", ""), 1)
        house_number = pynutil.insert('house: "') + house_number + pynutil.insert('"')

        # street moved to separate method given complexity
        street = self._get_street_fst()

        # suite moved to separate method given complexity
        suite = self._get_suite_fst()

        # town is just letters. can be multi-word, contain dash and end with coma
        town = pynini.closure(ALPHA, 1)
        # there can be a compositional town with dash, for ex. Wilkes-Barre
        town = town + pynini.closure(pynini.cross("-", " ") + town)
        # there can be multiple words in town name, town can optionally have comma at the end
        town = (
            town
            + pynini.closure(pynini.accep(" ") + pynutil.add_weight(town, 2.1))
            + pynini.closure(pynutil.delete(","), 0, 1)
        )
        town = pynutil.add_weight(
            pynutil.insert('town: "') + town + pynutil.insert('"'), 1.1
        )

        # state just comes from predefined mapping file, for ex.: CA, california
        state = load_mapping(
            get_data_file_path("address", "state.tsv"),
            key_case_agnostic=False,
            key_with_dot=False,
            val_case_agnostic=True,
        )
        state = pynutil.insert('state: "') + state + pynutil.insert('"')

        # regular zip is 5 digits
        zip = pynini.closure(DIGIT, 5, 5)
        # zip can have more 4-digit zip extension
        zip = zip + pynini.closure(
            pynutil.delete("-") + pynini.closure(DIGIT, 4, 4), 0, 1
        )
        # british zip can have letters
        british_zip_outcode = (
            pynini.closure(UPPER, 1, 2)
            + pynini.closure(DIGIT, 1, 2)
            + pynini.closure(UPPER, 0, 1)
        )
        british_zip_incode = DIGIT + UPPER + UPPER
        british_zip = (
            british_zip_outcode
            + pynini.closure(pynutil.delete(" "))
            + british_zip_incode
        )
        zip |= british_zip
        zip = pynutil.insert('zip: "') + zip + pynutil.insert('"')

        # combine house number and street
        house_street = pynini.closure(house_number + pynini.accep(" "), 0, 1) + street
        # combine suite, house number and street. suite can go before house and street
        suite_house_street = (
            suite + (pynini.accep(" ") | pynini.cross("-", " ")) + house_street
        )
        # or after
        suite_house_street |= (
            house_street
            + pynini.closure(pynutil.delete(","))
            + pynini.accep(" ")
            + suite
        )
        # or it can be absent
        suite_house_street |= house_street

        address = (
            suite_house_street
            + pynini.closure(pynini.accep(" ") + town, 0, 1)
            + pynini.closure(pynini.accep(" ") + state, 0, 1)
            + pynini.closure(pynini.accep(" ") + zip, 0, 1)
        )
        final_graph = self.add_tokens(address)
        self.fst = final_graph.optimize()

    @staticmethod
    def _get_street_fst():
        """
        street consists of name, type, pre/post direction
        """
        # street name is a sequence of letters, for ex. Aqua
        street_name = pynini.closure(ALPHA, 1)
        # there can be a dot at the end of street, for ex. "Neque."
        street_name = street_name + pynini.closure(pynutil.delete("."))
        # there can be a compositional street name with dash
        street_name = street_name + pynini.closure(pynini.cross("-", " ") + street_name)
        # there can be street name from multiple words
        street_name = street_name + pynini.closure(
            pynini.accep(" ") + pynutil.add_weight(street_name, 2.1)
        )
        street_name = (
            pynutil.insert('street_name: "') + street_name + pynutil.insert('"')
        )

        # Rd or rd. or Road, load mapping from a file
        street_type = load_mapping(
            get_data_file_path("address", "street_type.tsv"),
            key_case_agnostic=True,
            key_with_dot=True,
            val_case_agnostic=True,
        )
        street_type = (
            pynutil.insert('street_type: "') + street_type + pynutil.insert('"')
        )

        # N or north
        directional = load_mapping(
            get_data_file_path("address", "directional.tsv"),
            key_case_agnostic=True,
            key_with_dot=True,
            val_case_agnostic=True,
        )
        pre_directional = (
            pynutil.insert('pre_directional: "')
            + directional
            + pynutil.insert('"')
            + pynini.accep(" ")
        )
        post_directional = (
            pynini.accep(" ")
            + pynutil.insert('post_directional: "')
            + directional
            + pynutil.insert('"')
        )

        # street is combination of street name and street type
        street = street_name + pynini.accep(" ") + street_type
        street = (
            pynini.closure(pre_directional, 0, 1)
            + street
            + pynini.closure(post_directional, 0, 1)
        )
        return street

    @staticmethod
    def _get_suite_fst():
        """
        suite - some extra information that goes after house number and street.
        It could be apartment number or PO Box. suite consists of suite type and suite number.
        """

        # P.O. Box - special mark for just a post box, not actual address
        p = pynini.cross("p", "P") | pynini.accep("P") + pynini.closure(
            pynutil.delete(".")
        )
        o = pynini.cross("o", "O") | pynini.accep("O") + pynini.closure(
            pynutil.delete(".")
        )
        box = pynini.closure(LOWER | TO_LOWER, 3, 3) @ pynini.accep("box")
        po_box = p + pynini.closure(pynutil.delete(" ")) + o + pynini.accep(" ") + box

        # STE or APT - load possible suite types from a file
        suite_type = load_mapping(
            get_data_file_path("address", "suite_type.tsv"),
            key_case_agnostic=True,
            key_with_dot=True,
            val_case_agnostic=True,
        )
        suite_type |= po_box
        suite_type = pynutil.insert('suite_type: "') + suite_type + pynutil.insert('"')

        # optional prefix of suite number "#"
        suite_number_prefix = pynini.closure(
            pynutil.delete("#") + pynini.closure(pynutil.delete(" "), 0, 1), 0, 1
        )
        suite_number_digit = pynini.closure(DIGIT, 1)
        suite_number_alpha = UPPER | TO_UPPER
        # suite number be digits, upper-case letters or both
        suite_number = (
            suite_number_digit
            | suite_number_alpha
            | (suite_number_digit + suite_number_alpha)
        )
        suite_number = suite_number_prefix + suite_number
        suite_number = (
            pynutil.insert('suite_number: "') + suite_number + pynutil.insert('"')
        )

        # combine suite type and suite number, for ex.: Ap #32
        suite = suite_type + pynini.accep(" ") + suite_number
        # suite can just contain number, but with lower weight
        suite |= pynutil.add_weight(suite_number, 2.1)
        # it can be in reverse order: first number then type
        suite |= suite_number + pynini.accep(" ") + suite_type
        return suite
