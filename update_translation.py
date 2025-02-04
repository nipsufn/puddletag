# -*- coding: utf-8 -*-
import sys
import tempfile
from subprocess import call

import puddlestuff.resource
import puddlestuff.findfunc as findfunc
import puddlestuff.loadshortcuts as loadshortcuts
from puddlestuff.puddleobjects import PuddleConfig

usage = '''Usage: python update_translation.py [-h] [-q] language

Options:
    language: Locale of the language to be created eg. en_ZA, rus, fr_BE.
    -q Quiet mode (only error messages will be shown).
    -h Show this message.'''


def parse_dialogs():
    from puddlestuff.mainwin import (tagpanel, artwork, dirview,
                                     filterwin, storedtags, logdialog)
    import puddlestuff.masstag.dialogs as masstag
    import puddlestuff.mainwin.tagsources as tagsources
    import puddlestuff.mainwin.action_dialogs as action_dialogs

    def tr(s):
        s = s.replace('"', r'\"')
        return 'translate("Dialogs", "%s")' % s

    dialog_strings = []
    controls = [z.control for z in [tagpanel, artwork, dirview, filterwin,
                                    tagsources, storedtags, logdialog, masstag]]

    controls.extend(action_dialogs.controls)

    return [tr(c[0]) for c in controls]


def parse_functions():
    func_strings = []

    def tr(s):
        return 'translate("Functions", "%s")' % s.replace('"', r'\"')

    for f in findfunc.functions:
        try:
            x = findfunc.Function(f)
            if len(x.info) > 1:
                func_strings.append(tr(x.info[1]))
            func_strings.append(tr(x.funcname))
            for controls in x._getControls(None):
                del (controls[1])
                func_strings.extend(list(map(tr, controls)))
        except AttributeError:
            pass

    return func_strings


def parse_shortcuts():

    def tr(s):
        s = s.replace('"', r'\"')
        return 'translate("Menus", "%s")' % s

    f = tempfile.NamedTemporaryFile('rb+')
    fn = f.name

    loadshortcuts.check_file(fn, ':/shortcuts')
    cparser = PuddleConfig(fn)

    action_strings = []
    setting = cparser.data
    for section in cparser.sections():
        if section.startswith('shortcut'):
            values = dict([(str(k), v) for k, v in setting[section].items()])
            action_strings.append(tr(values['name']))
            if 'tooltip' in values:
                action_strings.append(tr(values['tooltip']))

    f.close()
    menus = tempfile.NamedTemporaryFile('rb+')
    fn = menus.name
    loadshortcuts.check_file(fn, ':/menus')
    cparser = PuddleConfig(fn)

    action_strings.extend(list(map(tr, cparser.data['menu'])))
    menus.close()

    return action_strings


def write_translations():
    f = open('puddlestuff/translations.py', 'r+')
    out = []
    for i, l in enumerate(f.readlines()):
        out.append(l)
        if 'translate("Menus", "Sort &By")' in l:
            break

    f.seek(len(''.join(out)))
    f.write('\n# Below here is generated by `update_translation.py`')
    f.write('\n    ' + '\n    '.join(parse_shortcuts()))
    f.write('\n\n    # Functions\n    ' + '\n    '.join(parse_functions()))
    f.write('\n\n    # Dialogs\n    ' + '\n    '.join(parse_dialogs()))
    f.write('\n')
    f.truncate()
    f.close()


verbose = True

try:
    lang = sys.argv[1]
    if lang.strip() == '-q':
        verbose = False
        lang = sys.argv[2]
except IndexError:
    print('Error: No language specified\n')
    print(usage)
    sys.exit(1)

if lang in ('--help', '-h'):
    print(usage)
    sys.exit(0)

# Update the qmake project file
with open('puddletag.pro', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith('TRANSLATIONS'):
        tr = ' translations/puddletag_%s.ts\n' % lang
        if tr.strip() not in line:
            lines[i] = line.strip() + tr
        break

with open('puddletag.pro', 'w') as f:
    f.writelines(lines)

if verbose:
    print('Updating `translations.py` from menu-/shortcut-/function-/dialog-sourcecode...\n')

write_translations()

try:
    if verbose:
        call(['pylupdate5', '-verbose', 'puddletag.pro'])
    else:
        call(['pylupdate5', 'puddletag.pro'])
except OSError:
    print('Error: pylupdate5 is not installed.')
    sys.exit(2)

if verbose:
    print('\nOpen %s in Qt Linguist in order to edit the translation.' % tr.strip())
