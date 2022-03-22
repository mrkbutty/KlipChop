#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# KlipChop menu function

import re

# All kllipchop customizable modules must have a main function
# The main function is passed three variables:
#   textlines   - Generator of clipboard lines
#   messagefunc - function to call with notification
#   config      - configuration dictionary
# The main function should return a string object or a list of strings

def main(textlines, messagefunc, config):
    """
    KlipChop func to convert hex numbers to decimal
    """
    # dp = locale.localeconv()['decimal_point']
    pattern = re.compile(f'^(0x)(^[a-z]+[\d]+^[a-z]+)', re.IGNORECASE)

    def convert(match):
        text = match.group()

        wb = len(text)
        text = format(int(text), 'x')
        if config['hexprefix']:
            text = '0x' + text
        wa = len(text)
        if wa < wb:
            text = ' ' * (wb - wa) + text
        return text

    result = list()
    count = 0
    for line in textlines(type='rawtext'):
        m = pattern.findall(line)
        count += len(m)
        line = pattern.sub(convert, line)
        result.append(line)

    result = ''.join(result)
    messagefunc(f'Converted {count} numbers to hex')
    return result