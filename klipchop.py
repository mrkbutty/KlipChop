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
from typing import DefaultDict
from pystray import Icon as icon, Menu as menu, MenuItem as menuitem
from PIL import Image
from pathlib import Path
from io import StringIO

import argh
import win32clipboard
import win32ui
import yaml
import texttable
from OuiLookup import OuiLookup


__author__ = "Mark Butterworth"
__copyright__ = "Copyright (C) 2021 Mark Butterworth"
__license__ = "MIT"
__version__ = '0.1.1 20211127'


# Setup later:
appname = None
configdir = None
configpath = None
# Default config:
config = {
    'sort': True,
    'separator': ',',
    'hexprefix': True,
    'overwrite': False,
}


def configload():
    global config

    with open(configpath, 'r') as fd:
        newconfig = yaml.safe_load(fd)
    config.update(newconfig)
    return


def configsave():
    global config
    dirname = Path(configpath).parent
    if not dirname.is_dir(): os.makedirs(dirname)
    with open(configpath, 'w') as fd:
        yaml.safe_dump(config, fd)


def get_clipboard():
    try:
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
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


def getOui(address):
    # for WWN remove first nibble, e.g. '50060E800882CC62' to '0060E800882CC62'
    return OuiLookup().query(address)


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


def get_lines():
    data = get_clipboard()
    for line in data.splitlines():
        line = line.strip().decode('utf-8', errors='ignore')
        if not line.isprintable():
            continue
        yield line


def action_uniquelines(icon, item):
    global sortflag
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
    icon.notify(f'{count} unique lines')
    

def action_lines2list(icon, item):
    global sortflag
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
    icon.notify(f'{count} unique lines converted into long CSV list.')


def action_splitlines(icon, item):
    global sortflag
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
    icon.notify(f'Text converted into {count} lines.')


def action_table2csv(icon, item):
    global sortflag
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
    icon.notify(f'Table converted into {count} CSV rows.')


def action_csv2table(icon, item):
    global sortflag
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
    icon.notify(f'CSV converted into {count} table rows.')


def action_ldev2list(icon, item):
    global sortflag
    pattern = re.compile('([0-9A-F]{4,6})', re.IGNORECASE)
    result = list()
    count = 0
    for line in get_lines():
        line = line.replace(':', '')
        m = pattern.search(line)
        if m:
            ldev = m.group(1)
            if len(ldev) == 6 and ldev.startswith('00'):
                ldev = ldev[2:]
            if ldev not in result:
                result.append(ldev)
                count += 1

    if config['sort']:
        result = sorted(result)
    result = config['separator'].join(result)
    set_clipboard(result)
    icon.notify(f'{count} LDEVs converted into long CSV list.')

    
def action_setsort(icon, item):
    global config
    config['sort'] = not config['sort']
    configsave()

def action_sethex(icon, item):
    global config
    config['hexprefix'] = not config['hexprefix']
    configsave()

def action_setsep(separator):
    global config
    config['separator'] = separator
    configsave()


def check_sep(separator):
    global config
    return config['separator'] == separator


def action_about(icon, item):
    win32ui.MessageBox(f'Version: {__version__}', appname)


def action_exit(icon, item):
    global config
    configsave()
    icon.stop()


def trayapp():
    global config, configdir, configpath, appname

    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app 
        # path into variable _MEIPASS'.
        application_path = Path(sys._MEIPASS)
    else:
        application_path = Path(__file__).absolute()

    appname = application_path.stem   # basename without extention

    configdir = Path.home() / f'.{appname}'
    configpath = configdir / f'{appname}.yaml'
    if configpath.exists():
        configload()

    image = Image.open('icon.png')

    sepmenu = menu(
        menuitem('Comma ","', lambda item: action_setsep(','), radio=True,
            checked=lambda item: check_sep(',')),
        menuitem('Space " "', lambda item: action_setsep(' '), radio=True,
            checked=lambda item: check_sep(' ')),
        menuitem('Semi-colon ";"', lambda item: action_setsep(';'), radio=True,
            checked=lambda item: check_sep(';')),
        menuitem('Forward-slash "/"', lambda item: action_setsep('/'), radio=True,
            checked=lambda item: check_sep('/')),
        menuitem('Back-slash "\\"', lambda item: action_setsep('\\'), radio=True,
            checked=lambda item: check_sep('\\')),
        menuitem('Bar "|"', lambda item: action_setsep('|'), radio=True,
            checked=lambda item: check_sep('|')),
    )

    mainmenu = menu( 
        menuitem('Unique lines', action_uniquelines),
        menuitem('Lines to unique CSV list', action_lines2list),
        menuitem('Split CSV text to lines', action_splitlines),
        menu.SEPARATOR,
        menuitem('Table to CSV (Converts bars "|" and dashes "-")', action_table2csv),
        menuitem('CSV to text table', action_csv2table),
        menu.SEPARATOR,
        menuitem('Hex to decimal', action_splitlines),
        menuitem('Decimal to Hex', action_splitlines),
        menu.SEPARATOR,
        menuitem('LDEV lines to unique CSV list', action_ldev2list),
        menuitem('WWN OUI to name', action_ldev2list),
        menu.SEPARATOR,
        menuitem('Sort results', action_setsort, checked=lambda x: config['sort']),
        menuitem('Prefix Hex with 0x', action_sethex, checked=lambda x: config['hexprefix']),
        menuitem('Separator', sepmenu),
        menu.SEPARATOR,
        menuitem('About', action_about),
        menuitem('Exit', action_exit),
        )

    app = icon(appname, image, menu=mainmenu)
    return app.run()


if __name__ == '__main__':
    trayapp()




