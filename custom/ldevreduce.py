#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# KlipChop menu function
import re


def nlist2ranges(values, hex=False):
    rlist = []

    hexwidth = 0
    for i in sorted(values, key=lambda x: int(x, 16) if hex else x):
        if hex:
            if len(i) > hexwidth: hexwidth = len(i)
            i = int(i, 16)
        if not rlist or rlist[-1][-1]+1 != i:
            rlist.append([i])
        else:
            rlist[-1].append(i)
    fmt = f'0{hexwidth}x' if hex else 'd'
    return [ f'{x[0]:{fmt}}' if len(x)==1 else f'{x[0]:{fmt}}-{x[-1]:{fmt}}' for x in rlist ]


# All kllipchop customizable modules must have a main function
# The main function is passed three variables:
#   textlines   - Generator of clipboard lines
#   messagefunc - function to call with notification
#   config      - configuration dictionary
# The main function should return a string object or a list of strings

def main(textlines, messagefunc, config):
    """
    KlipChop func
    """

    pattern = re.compile('([0-9A-F]{4,6})', re.IGNORECASE)
    result = list()
    count = 0
    for line in textlines():
        line = line.replace(':', '')
        m = pattern.findall(line)
        for ldev in m:
            if len(ldev) == 6 and ldev.startswith('00'):
                ldev = ldev[2:]
            if ldev not in result:
                result.append(ldev)
                count += 1

    if config['LDEV-ranges']:
        result = nlist2ranges(result, hex=True)
    elif config['sort']:
        result = sorted(result)
    
    result = config['separator'].join(result)
    messagefunc(f'{count} LDEVs converted into long CSV list.')
    return result

    