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
    KlipChop func to to convert ascii framed text table into CSV
    """
    result = list()
    count = 0
    pat_frameonly = re.compile(r'^[-+=\|\s]+$')
    pat_leftframe = re.compile(r'^\s*\|\s*')
    pat_rightframe = re.compile(r'\s*\|\s*$')
    pat_bars = re.compile(r'\s*\|\s*')
    altsep = '/' if config['separator'] == ',' else ','
    for line in textlines():
        if pat_frameonly.match(line):   # skip lines with frame only
            continue
        line = pat_leftframe.sub('', line)   # get rid of left frames
        line = pat_rightframe.sub('', line)   # get rid of right frames
        line = line.replace(config['separator'], altsep)   # change separators before insertion
        line = pat_bars.sub(config['separator'], line)   # change separators before insertion
        result.append(line)
        count += 1
    
    result = '\n'.join(result)
    messagefunc(f'Table converted into {count} CSV rows.')
    return result

