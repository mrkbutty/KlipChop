#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# KlipChop menu function


# All kllipchop customizable modules must have a main function
# The main function is passed three variables:
#   textlines   - Generator of clipboard lines
#   messagefunc - function to call with notification
#   config      - configuration dictionary
# The main function should return a string object or a list of strings

def main(textlines, messagefunc, config):
    """
    KlipChop func to to join lines together using the joiner character
    """
    result = list(textlines())
    count = len(result)
    result =  config['joiner'].join(result)

    messagefunc(f'Joined {count} lines')
    return result