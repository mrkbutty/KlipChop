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
from typing import DefaultDict
from pystray import Icon as icon, Menu as menu, MenuItem as menuitem
from PIL import Image
from pathlib import Path
import win32clipboard
import re
import yaml

__author__ = "Mark Butterworth"
__copyright__ = "Copyright (C) 2021 Mark Butterworth"
__license__ = "MIT"
__version__ = '0.1.0 20211126'


# Setup later:
configdir = None
configpath = None
# Default config:
config = {
    'sort': False,
}
# sortflag = False


def configload(filename):
    with open(filename, 'r') as fd:
        config = yaml.safe_load(fd)
    return config


def configsave(filename, configobj):
    dirname = Path(filename).parent
    if not dirname.is_dir(): os.makedirs(dirname)
    with open(filename, 'w') as fd:
        yaml.safe_dump(configobj, fd)


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

def getlines(data):
    for line in data.splitlines():
        line = line.strip().decode('utf-8', errors='ignore')
        if not line.isprintable():
            continue
        yield line


def action_lines2list(icon, item):
    global sortflag
    data = get_clipboard()
    result = list()
    count = 0
    for line in getlines(data):
        if line not in result:
            result.append(line)
            count += 1
    
    if config['sort']:
        result = sorted(result)
    result = ','.join(result)
    set_clipboard(result)
    icon.notify(f'{count} unique lines converted into long CSV list.')


def action_splitlines(icon, item):
    global sortflag
    data = get_clipboard()
    result = list()
    count = 0
    for line in getlines(data):
        if line not in result:
            result.extend(line.split(','))
            count += 1
    
    if config['sort']:
        result = sorted(result)
    count = len(result) 
    result = '\n'.join(result)
    set_clipboard(result)
    icon.notify(f'Text converted into {count} lines.')


def action_ldev2list(icon, item):
    global sortflag
    data = get_clipboard()
    pattern = re.compile('([0-9A-F]{4,6})', re.IGNORECASE)
    result = list()
    count = 0
    for line in getlines(data):
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
    result = ','.join(result)
    set_clipboard(result)
    icon.notify(f'{count} LDEVs converted into long CSV list.')

    
def action_sort(icon, item):
    global config
    config['sort'] = not config['sort']
    configsave(configpath, config)


def action_exit(icon, item):
    global config
    configsave(configpath, config)
    icon.stop()


def main():
    global config, configdir, configpath

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
        config = configload(configpath)

    image = Image.open('icon.png')
    menu = ( 
        menuitem('Lines to unique CSV list', action_lines2list),
        menuitem('Split CSV text to lines', action_splitlines),
        menuitem('LDEV lines to unique CSV list', action_ldev2list),
        menuitem('Sort results', action_sort, checked=lambda x: config['sort']),
        menuitem('Exit', action_exit),
        )

    trayapp = icon('Tufinator', image, menu=menu)
    trayapp.run()

if __name__ == '__main__':
    main()
