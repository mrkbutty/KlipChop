#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess

from cx_Freeze import setup, Executable
from git2version import gitversion

__appname__ = 'KlipChop',
__version__ = '1.0.0'
__description__ = 'Klip Chopping away...'
__icon__ = 'KlipChop.ico'

SETUPNAME = 'KlipChopSetup'
REPOROOT = '../KlipChop'
DISTDIR = '../KlipChop/dist'
# LICENSEDAYS = 90
INNO = 'C:/Program Files (x86)/Inno Setup 6/iscc'
ISSFILE = '../KlipChop/KlipChop.iss'


reporoot = os.path.abspath(REPOROOT)
absdist = os.path.abspath(DISTDIR)
print()
print(f'Using GIT repo: {reporoot}')
print(f'Distribution dir: {absdist}')
print()
gitver = gitversion(REPOROOT, errorstop=False, ignorechanges=True)
print(f'\nUsing git derived version: {gitver}')
setupfn = f'{SETUPNAME}_{gitver}'
print(f'Setup name: {setupfn}')
print()


command = None if len(sys.argv) < 2 else sys.argv[1].lower()
if command not in ('freeze', 'setup', 'both'):
    raise SystemExit('ERROR: specify: setup.py <freeze|setup|both>')


############### CX_FREEZE BUILD ###############

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {
    'build_exe': 'dist',   # directory to freeze into
    'packages': ['pystray'],
    'zip_include_packages': '*',
    'zip_exclude_packages': 'pystray',
    'excludes': ['tkinter'],
    'include_files': [ 
        'klipchop.png', 
        'klipchop.ico', 
        'README.md', 
        'LICENSE',
        'releasenotes.txt',
        ]
    }

import sys
gui = 'Win32GUI' if sys.platform=='win32' else None
cli = 'Console' if sys.platform=='win32' else None

executables = [
    Executable('KlipChop.py', base=gui, icon=__icon__),
    # Executable('app2.py', base=cli),
    # Executable('app3.py', base=gui),
]

if command in ('freeze', 'both'):
    sys.argv[1:] = [ 'build' ]
    setup(name = '__appname__',
        version = __version__,
        description = __description__,
        options = {'build_exe': build_options},
        executables = executables)


if command in ('setup', 'both'):
    # Update versiontag with correct info:
    with open(ISSFILE, 'r') as fd:
        isstext = fd.read()
    activeissfile = f'{ISSFILE}.last.iss'
    with open(activeissfile, 'w') as fd:
        isstext = isstext.replace('$versiontag$', gitver)
        isstext = fd.write(isstext)

    print('Creating ')
    completed = subprocess.run([INNO, f'/F{setupfn}', activeissfile])
    completed.check_returncode()