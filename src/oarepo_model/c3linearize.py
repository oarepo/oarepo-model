#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""C3 linearization module.

This module is used to check mro consistency of a class without explicitly constructing the class.
"""

from __future__ import annotations


class LinearizationError(ValueError):
    """Represents an error occurring during the linearization process."""


def merge(sequences: list[list[type]]) -> list[type]:
    """Merge object sequences preserving order in initial sequences.

    This is the merge function as described for C3, see:
    http://www.python.org/download/releases/2.3/mro/

    """
    # Make sure we don't actually mutate anything we are getting as input.
    sequences = [list(x) for x in sequences]

    result: list[type] = []

    while True:
        # Clear out blank sequences.
        sequences = [x for x in sequences if x]
        if not sequences:
            return result

        # Find the first clean head.
        for seq in sequences:
            head = seq[0]
            # If this is not a bad head (ie. not in any other sequence)...
            if not any(head in s[1:] for s in sequences):
                break
        else:
            raise LinearizationError("inconsistent hierarchy")

        # Move the head from the front of all sequences to the end of results.
        result.append(head)
        for seq in sequences:
            if seq[0] == head:
                del seq[0]


def mro_without_class_construction(cls_list: list[type]) -> list[type]:
    """Return the MRO of the class list without constructing the class."""
    return merge([x.mro() for x in cls_list])
