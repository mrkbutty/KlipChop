#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# KlipChop menu function

import locale
import re


# All kllipchop customizable modules must have a main function
# The main function is passed three variables:
#   textlines   - Generator of clipboard lines
#   messagefunc - function to call with notification
#   config      - configuration dictionary
# The main function should return a string object or a list of strings

def main(textlines, messagefunc, config):
    """
    KlipChop func to sum up etc numbers
    """
    dp = locale.localeconv()['decimal_point']
    pattern = re.compile(f'(0x[\da-f]+|\d+\.?\d*|\.\d+)', re.IGNORECASE)

    def numfinder(dp=None):
        for line in textlines():
            if dp:
                line = line.replace(dp, '.')   # change from locale decimal sep to normnal

            m = pattern.findall(line)
            for n in m:
                if '.' in n:
                    yield float(n)
                elif n.lower().startswith('0x'):
                    yield int(n, 16)
                else:
                    yield int(n)

    numbers = list(numfinder())  # try looking for normal first
    if not numbers and dp != '.':   # else try using locale decimal point
        numbers = list(numfinder(dp))

    count = len(numbers)
    tot = sum(numbers)
    mean = tot / count if count > 0 else 0
    result = f'Count: {count:,d}\nsum: {tot:,f}\naverage: {mean:,f}\nmin: {min(numbers):,f}\nmax: {max(numbers):,f}\n'
    messagefunc(result)
    return result
