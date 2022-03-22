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
    KlipChop func to to convert lines into a CSV list
    """
    result = list()
    count = 0
    for line in textlines():
        if line not in result:
            result.append(line)
            count += 1
    
    if config['sort']:
        result = sorted(result)
    result = config['separator'].join(result)
    messagefunc(f'{count} unique lines converted into long CSV list.')
    return result
