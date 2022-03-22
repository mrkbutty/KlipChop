#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# KlipChop menu function

import texttable

# def make_table (table, frameH = '-', frameV = '|', frameX = '+'):
#     cols = [list(x) for x in zip(*table)]
#     lengths = [max(map(len, map(str, col))) for col in cols]
#     f = frameV + frameV.join(' {:>%d} ' % l for l in lengths) + frameV
#     s = frameX + frameX.join(frameH * (l+2) for l in lengths) + frameX

#     output = StringIO()
#     output.write(s)
#     for row in table:
#         output.write(f.format(*row))
#         output.write(s)
#     return output


# All kllipchop customizable modules must have a main function
# The main function is passed three variables:
#   textlines   - Generator of clipboard lines
#   messagefunc - function to call with notification
#   config      - configuration dictionary
# The main function should return a string object or a list of strings

def main(textlines, messagefunc, config):
    """
    KlipChop func to to convert CSV into ascii framed table
    """
    count = 0
    result = ''
    tables = list()
    rows = list()
    lastlen = 0
    for line in textlines():
        if line and line not in result:
            cols = line.split(config['separator'])
            if lastlen and lastlen != len(cols):
                tables.append(rows)
                rows = list()
            lastlen = len(cols)
            rows.append(cols)
            count += 1
    tables.append(rows)
        
    for t in tables:
        # transposed list of col lengths:
        transpose = [ list(map(len, x)) for x in list(map(list, zip(*t))) ]
        maxw = list(map(max, transpose))
        table = texttable.Texttable()
        table.set_cols_width(maxw)
        table.set_cols_dtype([ 't' ] * len(maxw))
        table.add_rows(t)
        result += table.draw()
        result += '\n'

    messagefunc(f'CSV converted into {count} table rows.')
