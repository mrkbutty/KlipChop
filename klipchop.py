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

import importlib
import sys
import os
import re
import locale
import importlib.util
import traceback

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
__version__ = '1.0.0 20220322'


# Setup later:
progdir = None
configdir = None
configpath = None

# Default config:
config = {
    'separator': ',',
    'joiner': ' ',
    'sort': True,
    'hexprefix': True,
    'overwrite': False,
    'LDEV-ranges': True,
}

# Generator functions to make callables for menu items:
def toggle_bool(name):
    def inner(icon, item):
        global config
        config[name] = not config[name]
        configsave()
    return inner

def get_bool(name):
    def inner(item):
        return config[name]
    return inner

sepmenu = st.Menu(
    st.MenuItem('Comma ","', lambda: setsep(','), radio=True,
        checked=lambda _: current_sep(',')),
    st.MenuItem('Comma space ", "', lambda: setsep(', '), radio=True,
        checked=lambda _: current_sep(', ')),
    st.MenuItem('Space " "', lambda: setsep(' '), radio=True,
        checked=lambda _: current_sep(' ')),
    st.MenuItem('Semi-colon ";"', lambda: setsep(';'), radio=True,
        checked=lambda _: current_sep(';')),
    st.MenuItem('Forward-slash "/"', lambda: setsep('/'), radio=True,
        checked=lambda _: current_sep('/')),
    st.MenuItem('Back-slash "\\"', lambda: setsep('\\'), radio=True,
        checked=lambda _: current_sep('\\')),
    st.MenuItem('Bar "|"', lambda: setsep('|'), radio=True,
        checked=lambda _: current_sep('|')),
)

joinmenu = st.Menu(
    st.MenuItem('Space " "', lambda: setjoin(' '), radio=True,
        checked=lambda _: current_join(' ')),
    st.MenuItem('Comma ","', lambda: setjoin(','), radio=True,
        checked=lambda _: current_join(',')),
    st.MenuItem('Comma space ", "', lambda: setjoin(', '), radio=True,
        checked=lambda _: current_join(', ')),
    st.MenuItem('Semi-colon ";"', lambda: setjoin(';'), radio=True,
        checked=lambda _: current_join(';')),
    st.MenuItem('Forward-slash "/"', lambda: setjoin('/'), radio=True,
        checked=lambda _: current_join('/')),
    st.MenuItem('Back-slash "\\"', lambda: setjoin('\\'), radio=True,
        checked=lambda _: current_join('\\')),
    st.MenuItem('Bar "|"', lambda: setjoin('|'), radio=True,
        checked=lambda _: current_join('|')),
)


optmenuitems = [
    # st.MenuItem('Open custom script directory', action_customdir),
    st.MenuItem('Set default separator', sepmenu),
    st.MenuItem('Set default joiner', joinmenu),
    st.MenuItem('Sort results', lambda: toggle_bool('sort'), checked=get_bool('sort')),
    st.MenuItem('Prefix Hex with 0x', lambda: toggle_bool('hexprefix'), checked=get_bool('hexprefix')),
]

# Global for the dynamically loaded modules:
moddict = dict()


# Config file handling
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


def readmenuconfig(filename):
    '''read a menuconfig from either the transform or custom directories'''
    global config, optmenuitems

    currentdir = Path(filename).absolute().parent
    menu = list()
    with open(filename) as fd:
        for line in fd.readlines():
            line = line.strip()
            if not line or line.startswith('#'): continue
            if line.startswith('@'): # include another menu
                include = currentdir / line.strip('@')
                if include.is_file():
                    menu.extend(readmenuconfig(include))
            elif line.startswith('$'): # add option to config
                line = line.strip('$')
                parts = [ i.strip() for i in line.split('=', 3) ]
                if len(parts) == 4:
                    (name, opttype, default, params) = parts
                    if opttype == 'bool':
                        config[name] = config.get(name, default)
                        optmenuitems.append(st.MenuItem(params, toggle_bool(name), checked=get_bool(name)))
            elif line.startswith('---'): # add a seperator
                menu.append(('---', None))
            else:
                parts = [ x.strip() for x in line.split(':', 1) ]
                if len(parts) == 2:
                    name, description = parts
                    fullpath = currentdir / name
                    if fullpath.is_file():
                        menu.append((str(fullpath), description))
    return menu


def get_clipboard_text():
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


def set_clipboard_text(text):
    if isinstance(text, list):
        text = '\n'.join(text)
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
    except TypeError as exc:
        print(exc)
        return # it's not text so ignore
    finally:
        win32clipboard.CloseClipboard()


def readdata(type=None):
    # Only supports text (at the moment)
    data = get_clipboard_text()
    if type == 'rawtext':
        yield data
    else:   # defaults to yielding lines of stripped text:
        for line in data.splitlines():
            line = line.strip()   #.decode('utf-8', errors='ignore')
            # if not line.isprintable():  # No longer needed as clipboard bug fixed above
            #     continue
            yield line

    
def action_setsort(icon, item):
    config['sort'] = not config['sort']
    configsave()

def action_sethex(icon, item):
    config['hexprefix'] = not config['hexprefix']
    configsave()

def setsep(separator):
    config['separator'] = separator
    configsave()

def current_sep(separator):
    return config['separator'] == separator

def setjoin(joiner):
    config['joiner'] = joiner
    configsave()

def current_join(joiner):
    return config['joiner'] == joiner

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


def runmodule(icon, item):
    global config

    # text = list(readdata())
    try:
        result = moddict[item.text].main(readdata, icon.notify, config)
    except Exception as exc:
            win32ui.MessageBox(f'Error running {item.text}:\n\n{traceback.format_exc()}\n', __appname__)

    set_clipboard_text(result)


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


def trayapp(menudef):

    global moddict
    image = Image.open(progdir / f'{__appname__}.png')

    optmenu = st.Menu(*optmenuitems)
    
    menuitems = list()
    for filename, description in menudef:
        if filename.startswith('---'):
            menuitems.append(st.Menu.SEPARATOR)
        else:
            # Dynamic import
            spec = importlib.util.spec_from_file_location('module.name', filename)
            moddict[description] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(moddict[description])
            menuitems.append(st.MenuItem(description, lambda icon, item: runmodule(icon, item)))
    menuitems.extend( [st.Menu.SEPARATOR,
            st.MenuItem('Options', optmenu),
            st.MenuItem('About', action_about),
            st.MenuItem('Exit', action_exit),
        ] )

    traymenu = st.Menu(*menuitems) 

    app = st.Icon(__appname__, image, menu=traymenu)
    return app.run()


def klipchop():
    global progdir, configdir, configpath

    progdir = Path(getprogdir())

    configdir = Path.home() / f'.{__appname__}'
    configpath = configdir / f'{__appname__}.yaml'
    if configpath.exists():
        configload()

    menu = readmenuconfig(progdir / 'transforms' / 'menu.config')
    devcustom = progdir / 'custom' / 'menu.config'
    prodcustom = configdir / 'custom' / 'menu.config'
    if devcustom.is_file():  # use dev custom directory in development mode only.
        menu.extend(readmenuconfig(devcustom))
    elif prodcustom.is_file():
        menu.extend(readmenuconfig(prodcustom))

    trayapp(menu)


if __name__ == '__main__':
    klipchop()





