"""
Text normalization rules for english are adapted from NVIDIA:
https://github.com/NVIDIA/NeMo/tree/main/nemo_text_processing/text_normalization/en

Classification
--------------

1st step splits text into tokens and classifies tokens into semiotic classes.
this is a big FST that converts input text to a tagged sequence:

..

    "12/04/15 at 3:30pm!"

    { left_punct: "\"" date { month: "december" day: "4" year: "15" } } tokens { name: "at" }
    tokens { time { hours: "3" minutes: "30" suffix: "PM" } right_punct: "!\"" }

.. automodule:: en_us_normalization.production.classify

Verbalization
-------------

Tagged tokens are parsed with `text_normalization` and semiotic classes are passed
for verbalization. During verbalization, serialized tokens are converted to spoken form:

..

    date|month:december|day:4|year:15|

    december fourth fifteen

.. automodule:: en_us_normalization.production.verbalize

"""
