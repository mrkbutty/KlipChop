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
    KlipChop func to to convert text into unique lines
    """
    counter = dict()

    for line in textlines():
        counter[line] = counter.get(line, 0) + 1
    
    if config['sort']:
        countsort = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        result = [ f'{x} #{y}' for x,y in countsort]
    else:
        result = [ f'{x} #{y}' for x,y in counter.items()]

    result = '\n'.join(result)
    messagefunc(f'{len(counter.keys())} unique lines')
    return result