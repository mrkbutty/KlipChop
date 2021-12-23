#! /usr/bin/env python3
# -*- coding: utf-8 -*-

# KlipChop.py - Generates Charts from Hitachi Storage export data.

# MIT License

# Copyright (c) 2021 Mark Butterworth

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
KlipChop.py  - Tray app to assist with clipboard operations.
"""

import sys
import os
import re
import locale
from typing import DefaultDict
# from pystray import Icon as icon, Menu as menu,.MenuItem as.MenuItem
from PIL import Image
from pathlib import Path
from io import StringIO

import win32clipboard
import win32ui

import pystray as st
import yaml
import texttable



__appname__ = 'KlipChop'
__author__ = "Mark Butterworth"
__email__ = 'mark@markbutterworth.net'
__copyright__ = "Copyright (C) 2021 Mark Butterworth"
__license__ = "MIT"
__version__ = '0.1.5 20212120'


# Setup later:
configdir = None
configpath = None
# Default config:
config = {
    'sort': True,
    'separator': ',',
    'hexprefix': True,
    'overwrite': False,
    'LDEV-ranges': True,
}


def configload():
    global config

    with open(configpath, 'r') as fd:
        newconfig = yaml.safe_load(fd)
    config.update(newconfig)
    return


def configsave():
    dirname = Path(configpath).parent
    if not dirname.is_dir(): os.makedirs(dirname)
    with open(configpath, 'w') as fd:
        yaml.safe_dump(config, fd)


def get_clipboard():
    try:
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        # Below helps with a bug in getting excel clipboard data
        # See: https://stackoverflow.com/questions/66756315/using-win32clipboard-getclipboarddata-to-get-copied-excel-table-returns-chinese
        # it's using the size of the memory structure to determine how many bytes are in it.
        # However, the documentation for the clipboard formats states this:
        # CF_TEXT: Text format. Each line ends with a carriage return/linefeed (CR-LF) combination. A null character signals the end of the data. Use this format for ANSI text.
        # CF_UNICODETEXT: Unicode text format. Each line ends with a carriage return/linefeed (CR-LF) combination. A null character signals the end of the data.
        if '\x00' in data:
            data = data[:data.find('\x00')]
    except TypeError as exc:
        print(exc)
        return None # it's not text so ignore
    finally:
        win32clipboard.CloseClipboard()
    return data


def set_clipboard(text):
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
    except TypeError as exc:
        print(exc)
        return # it's not text so ignore
    finally:
        win32clipboard.CloseClipboard()


def get_lines():
    data = get_clipboard()
    for line in data.splitlines():
        line = line.strip()   #.decode('utf-8', errors='ignore')
        # if not line.isprintable():  # No longer needed as clipboard bug fixed above
        #     continue
        yield line


def make_table (table, frameH = '-', frameV = '|', frameX = '+'):
    cols = [list(x) for x in zip(*table)]
    lengths = [max(map(len, map(str, col))) for col in cols]
    f = frameV + frameV.join(' {:>%d} ' % l for l in lengths) + frameV
    s = frameX + frameX.join(frameH * (l+2) for l in lengths) + frameX

    output = StringIO()
    output.write(s)
    for row in table:
        output.write(f.format(*row))
        output.write(s)
    return output


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


def action_uniquelines(icon, item):
    result = list()
    count = 0
    for line in get_lines():
        if line not in result:
            result.append(line)
            count += 1
    
    if config['sort']:
        result = sorted(result)
    result = '\n'.join(result)
    set_clipboard(result)
    icon.notify(f'{count} unique lines', __appname__)
    

def action_lines2list(icon, item):
    result = list()
    count = 0
    for line in get_lines():
        if line not in result:
            result.append(line)
            count += 1
    
    if config['sort']:
        result = sorted(result)
    result = config['separator'].join(result)
    set_clipboard(result)
    icon.notify(f'{count} unique lines converted into long CSV list.', __appname__)


def action_splitlines(icon, item):
    result = list()
    count = 0
    for line in get_lines():
        if line not in result:
            result.extend(line.split(config['separator']))
            count += 1
    
    if config['sort']:
        result = sorted(result)
    count = len(result) 
    result = '\n'.join(result)
    set_clipboard(result)
    icon.notify(f'Text converted into {count} lines.', __appname__)


def action_table2csv(icon, item):
    result = list()
    count = 0
    pat_frameonly = re.compile(r'^[-+=\|\s]+$')
    pat_leftframe = re.compile(r'^\s*\|\s*')
    pat_rightframe = re.compile(r'\s*\|\s*$')
    pat_bars = re.compile(r'\s*\|\s*')
    altsep = '/' if config['separator'] == ',' else ','
    for line in get_lines():
        if pat_frameonly.match(line):   # skip lines with frame only
            continue
        line = pat_leftframe.sub('', line)   # get rid of left frames
        line = pat_rightframe.sub('', line)   # get rid of right frames
        line = line.replace(config['separator'], altsep)   # change separators before insertion
        line = pat_bars.sub(config['separator'], line)   # change separators before insertion
        result.append(line)
        count += 1
    
    result = '\n'.join(result)
    set_clipboard(result)
    icon.notify(f'Table converted into {count} CSV rows.', __appname__)


def action_csv2table(icon, item):
    count = 0
    result = ''
    tables = list()
    rows = list()
    lastlen = 0
    for line in get_lines():
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

    set_clipboard(result)
    icon.notify(f'CSV converted into {count} table rows.', __appname__)


def action_hex2dec(icon, item):
    icon.notify('Not yet implemented', __appname__)


def action_dec2hex(icon, item):
    icon.notify('Not yet implemented', __appname__)


def action_ldev2list(icon, item):
    pattern = re.compile('([0-9A-F]{4,6})', re.IGNORECASE)
    result = list()
    count = 0
    for line in get_lines():
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
    set_clipboard(result)
    icon.notify(f'{count} LDEVs converted into long CSV list.', __appname__)


def action_wwnoui(icon, item, extractflag):
    icon.notify('Not yet implemented', __appname__)


def action_calculate(icon, item):
    dp = locale.localeconv()['decimal_point']
    pattern = re.compile(f'(0x[\da-f]+|\d+\.?\d*|\.\d+)', re.IGNORECASE)

    def numfinder(dp=None):
        for line in get_lines():
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
    mean = tot / count if count > 0 else 'NA'
    result = f'Count:{count:,d}\nsum:{tot:,f}\naverage:{mean:,f}\nmin:{min(numbers):,f}\nmax:{max(numbers):,f}\n'
    set_clipboard(result)
    icon.notify(result, __appname__)

    
def action_setsort(icon, item):
    config['sort'] = not config['sort']
    configsave()

def action_sethex(icon, item):
    config['hexprefix'] = not config['hexprefix']
    configsave()

def action_setsep(separator):
    config['separator'] = separator
    configsave()


def current_sep(separator):
    return config['separator'] == separator


def action_about(icon, item):
    win32ui.MessageBox(f'''
Version: {__version__}

Python:{sys.version}

Progdir:{getprogdir()}

Any ideas for repeated mundane clipboard tasks?
Contact: {__email__}
''', __appname__)


def action_exit(icon, item):
    global config
    configsave()
    icon.stop()


def getprogdir():
    """ 
    If the application is run as a bundle, the PyInstaller bootloader
    extends the sys module by a flag frozen=True and sets the app 
    path into variable _MEIPASS'.  Cx_freeze requires lookup of the sys.execuatable
    PyInstaller Version 5.0 will change to __file__ as a full abspath. 
    """
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))


def trayapp():
    global configdir, configpath

    progdir = Path(getprogdir())

    configdir = Path.home() / f'.{__appname__}'
    configpath = configdir / f'{__appname__}.yaml'
    if configpath.exists():
        configload()

    image = Image.open(progdir / f'{__appname__}.png')


    sepmenu = st.Menu(
        st.MenuItem('Comma ","', lambda: action_setsep(','), radio=True,
            checked=lambda _: current_sep(',')),
        st.MenuItem('Comma space ", "', lambda: action_setsep(', '), radio=True,
            checked=lambda _: current_sep(', ')),
        st.MenuItem('Space " "', lambda: action_setsep(' '), radio=True,
            checked=lambda _: current_sep(' ')),
        st.MenuItem('Semi-colon ";"', lambda: action_setsep(';'), radio=True,
            checked=lambda _: current_sep(';')),
        st.MenuItem('Forward-slash "/"', lambda: action_setsep('/'), radio=True,
            checked=lambda _: current_sep('/')),
        st.MenuItem('Back-slash "\\"', lambda: action_setsep('\\'), radio=True,
            checked=lambda _: current_sep('\\')),
        st.MenuItem('Bar "|"', lambda: action_setsep('|'), radio=True,
            checked=lambda _: current_sep('|')),
    )

    mainmenu = st.Menu(
        st.MenuItem('Unique lines', action_uniquelines), # default=True),
        st.MenuItem('Lines to unique CSV list', action_lines2list),
        st.MenuItem('Split CSV text to lines', action_splitlines),
        st.Menu.SEPARATOR,
        st.MenuItem('Table to CSV (converts ascii framed text)', action_table2csv),
        st.MenuItem('CSV to text table (and the reverse)', action_csv2table),
        st.Menu.SEPARATOR,
        st.MenuItem('Hex to decimal', action_hex2dec),
        st.MenuItem('Decimal to Hex', action_dec2hex),
        st.Menu.SEPARATOR,
        st.MenuItem('LDEV reduced to unique list', action_ldev2list),
        st.MenuItem('Annotate WWN/NAA OUI', lambda icon,item: action_wwnoui(icon, item, False)),
        st.MenuItem('Extract WWN/NAA OUI', lambda icon,item: action_wwnoui(icon, item, True)),
        st.Menu.SEPARATOR,
        st.MenuItem('Calculator (count, sum, min, max, average, median)', action_calculate),
        st.Menu.SEPARATOR,
        st.MenuItem('Sort results', action_setsort, checked=lambda x: config['sort']),
        st.MenuItem('Prefix Hex with 0x', action_sethex, checked=lambda x: config['hexprefix']),
        st.MenuItem('Reduce LDEV ranges', action_setsort, checked=lambda x: config['LDEV-ranges']),
        st.MenuItem('Separator', sepmenu),
        st.Menu.SEPARATOR,
        st.MenuItem('About', action_about),
        st.MenuItem('Exit', action_exit),
        )

    app = st.Icon(__appname__, image, menu=mainmenu)
    return app.run()


if __name__ == '__main__':
    trayapp()




