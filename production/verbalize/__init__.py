"""
Verbalization rules
===================

Rules to convert semiotic classes into spoken form.
Regular words are not passed for verbalization.
Each semiotic class has predefined set of fields, that
verbalization grammar should take care of.
Verbalization grammars drop field names and transduce field values
into words.

Combining everything together into single FST:

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: class.rst

    VerbalizeFst

Rules for verbalization of different semiotic classes:

.. autosummary::
    :toctree: generated/
    :nosignatures:
    :template: class.rst

    CardinalFst
    OrdinalFst
    DecimalFst
    FractionFst
    RomanFst
    DateFst
    VerbatimFst
    ElectronicFst
    MeasureFst
    MoneyFst
    TimeFst

"""

from en_us_normalization.production.verbalize.address import AddressFst
from en_us_normalization.production.verbalize.cardinal import CardinalFst
from en_us_normalization.production.verbalize.date import DateFst
from en_us_normalization.production.verbalize.decimal import DecimalFst
from en_us_normalization.production.verbalize.electronic import ElectronicFst
from en_us_normalization.production.verbalize.fraction import FractionFst
from en_us_normalization.production.verbalize.measure import MeasureFst
from en_us_normalization.production.verbalize.money import MoneyFst
from en_us_normalization.production.verbalize.ordinal import OrdinalFst
from en_us_normalization.production.verbalize.roman import RomanFst
from en_us_normalization.production.verbalize.telephone import TelephoneFst
from en_us_normalization.production.verbalize.time import TimeFst
from en_us_normalization.production.verbalize.verbatim import VerbatimFst
