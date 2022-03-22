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
    KlipChop func to to convert CSV into seperate lines
    """
    result = list()
    count = 0
    for line in textlines():
        if line not in result:
            result.extend(line.split(config['separator']))
            count += 1
    
    if config['sort']:
        result = sorted(result)
    count = len(result) 
    result = '\n'.join(result)
    messagefunc(f'Text converted into {count} lines.')
    return result

