########################################################################
# Acid Vault                                                           #
#                                                                      #
# This program is free software: you can redistribute it and/or modify #
# it under the terms of the GNU Affero General Public License as       #
# published by the Free Software Foundation, either version 3 of the   #
# License, or (at your option) any later version.                      #
#                                                                      #
# This program is distributed in the hope that it will be useful,      #
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
# GNU Affero General Public License for more details.                  #
#                                                                      #
# You should have received a copy of the GNU Affero General Public     #
# License along with this program.  If not, see                        #
# <http://www.gnu.org/licenses/>.                                      #
########################################################################
'''Varius GUI widgets'''
import datetime
from distutils.version import LooseVersion
import json
import os
import subprocess
import sys
import tkinter
import urllib.request
import uuid

from ..helpers.version import __version__, __author__, __email__  # noqa:F401,E501 These are actually used
from ..helpers.version import __license__, __uri__, __summary__  # noqa:F401,E501 These are actually used
from ..vault import generate_password
from ..vault import VALID_PASSWORD_TYPES

DEFAULT_PROFILE = {
            'attributes': {
                'ssh_config': {
                    'host': '',
                    'port': '',
                    'username': '',
                    'password': '',
                    'clear_on_exit': True},
                'file_config': {
                    'sync': True,
                    'file_location': '',
                    'original_file': '',
                    'use_steganography': False,
                    'clear_on_exit': True},
                'last_update': None},
            'widgets': {'file_location': 'Local'}}

class Dialog(tkinter.Toplevel):
    """
    Parent Dialog frame, inherit and override
    body and apply methods.
    """
    def __init__(self, parent, title=None, initial_data=None):
        super().__init__(parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = tkinter.ttk.Frame(self)
        self.initial_focus = self.body(body, initial_data)
        body.pack(padx=5, pady=5, fill=tkinter.BOTH)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    def body(self, master, initial_data=None):
        """Body of dialog, override in child classes."""
        pass

    def buttonbox(self):
        """Standard OK and Cancel buttons."""
        box = tkinter.ttk.Frame(self)

        w = tkinter.ttk.Button(
            box, text="OK", width=10, command=self.ok, default=tkinter.ACTIVE)
        w.pack(side='left', padx=5, pady=5)
        w = tkinter.ttk.Button(
            box, text="Cancel", width=10, command=self.cancel)
        w.pack(side='left', padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()
        return box

    def ok(self, event=None):
        """On OK button press."""
        if not self.validate():
            self.initial_focus.focus_set()
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):
        """On Cancel button press."""
        self.parent.focus_set()
        self.destroy()

    def validate(self):
        """
        Validate action on close, defaults to True if not overridden.
        """
        return 1

    def apply(self):
        """Apply result on OK button press, override in child class."""
        pass


class EditProfiles(Dialog):
    """Dialog to edit profiles."""
    def body(self, master, initial_data):
        self.profiles = []
        self.top = tkinter.Frame(master)
        middle = tkinter.Frame(master)
        bottom = tkinter.Frame(master)
        for profile in sorted(initial_data):
            self.add(profile)
        self.status = tkinter.StringVar()
        tkinter.Label(middle, textvar=self.status).pack(side='left')
        tkinter.Button(bottom, command=self.add, text='Add').pack()
        self.top.pack()
        middle.pack()
        bottom.pack()

    def add(self, data=''):
        f = tkinter.Frame(self.top)
        entry_data = tkinter.StringVar()
        entry_data.set(data)
        f.entry_data = entry_data
        f.original_value = data
        f.remove = tkinter.BooleanVar()
        e = tkinter.Entry(f, textvariable=entry_data)
        c = tkinter.Checkbutton(f, text='Remove', variable=f.remove)
        f.pack(side='top')
        e.pack(side='left')
        c.pack(side='left')
        self.profiles.append(f)

    def validate(self):
        found = []
        for profile in self.profiles:
            data = profile.entry_data.get()
            if not data:
                self.status.set('Empty profile names detected!')
                return False
            elif data in found:
                self.status.set('Duplicate profile name detected!')
                return False
            found.append(data)
        return True

    def apply(self):
        rename = {}
        keep = []
        for profile in self.profiles:
            if profile.remove.get():
                continue
            new_val = profile.entry_data.get()
            old_val = profile.original_value
            if old_val and new_val != old_val:
                rename[old_val] = new_val
            elif new_val:
                keep.append(new_val)
        self.result = {'rename': rename,
                       'keep': keep,
                       }
        
            

class AddPassword(Dialog):
    '''Add/Edit password dialog.'''
    def body(self, master, initial_data):
        """Body of set key dialog."""
        self.timer = Timer(master, self.close, 5000*60)
        master.bind_all('<Enter>', self.timer.reset)
        self.initial_data = initial_data
        if initial_data and len(initial_data) == 6:
            self.uid = uuid.UUID(initial_data[0])
            start = 2
        else:
            self.uid = uuid.uuid4()
            start = 0
        for index, key in enumerate(('system',
                                     'username',
                                     'password',
                                     'notes'),
                                    start=start):
            setattr(self, key, tkinter.StringVar())
            e = LabelEntry(master,
                           width=50,
                           label=key.title(),
                           textvariable=getattr(self, key))
            e.pack()
            if initial_data:
                getattr(self, key).set(initial_data[index])

        f = tkinter.Frame(master)
        f.pack()
        pw_type = tkinter.StringVar()
        pw_type.set(VALID_PASSWORD_TYPES[0])
        pw_len = tkinter.IntVar()
        pw_len.set(10)
        gen_pass = tkinter.OptionMenu(f, pw_type, *VALID_PASSWORD_TYPES)
        gen_pass.configure(width=20)
        length = tkinter.OptionMenu(f, pw_len, *range(4, 16))
        length.configure(width=2)

        gen_pass.pack(side='left')
        length.pack(side='left')
        b = tkinter.Button(
            f,
            text='Generate Password',
            command=lambda: self.password.set(
                generate_password(
                    pw_type.get(), pw_len.get())))
        b.pack(side='left')

    def apply(self):
        """Set result upon OK button press."""
        # Only return result if it has changed.
        result = (self.uid,
                  datetime.datetime.utcnow(),
                  self.system.get(),
                  self.username.get(),
                  self.password.get(),
                  self.notes.get())
        if self.initial_data and len(self.initial_data) == len(result):
            if [index for index in range(2, 6) if
                    result[index] != self.initial_data[index]]:
                self.result = result
        else:
            self.result = result

    def close(self):
        self.timer.stop()
        self.destroy()


class SetupSSH(Dialog):
    '''Setup SSH related settings.'''
    def body(self, master, initial_data):
        """Body of SSH settings dialog."""
        self.clear_on_exit = tkinter.BooleanVar()
        self.clear_on_exit.set(initial_data.get('clear_on_exit', True))
        clear_on_exit = tkinter.Checkbutton(master,
                                            text='Clear SSH settings on exit',
                                            variable=self.clear_on_exit,
                                            anchor='w')
        clear_on_exit.pack(expand=1, fill=tkinter.X)
        for key in ('host', 'port', 'username', 'password'):
            setattr(self, key, tkinter.StringVar())
            e = LabelEntry(master,
                           width=50,
                           label=key.title().replace('_', ' '),
                           textvariable=getattr(self, key))
            e.pack()
            if key == 'password':
                e.set_config(show='*')
            if initial_data:
                try:
                    getattr(self, key).set(initial_data[key])
                except KeyError:
                    pass

    def apply(self):
        """Set result upon OK button press."""
        self.result = {key: getattr(self, key).get() for
                       key in ('host', 'port', 'username',
                               'password', 'clear_on_exit')}


class SetupFiles(Dialog):
    '''File related settings, paths and steganography.'''
    def body(self, master, initial_data):
        # Checkboxes.
        for key, default in (('use_steganography', False),
                             ('clear_on_exit', True),
                             ('sync', True)):
            value = initial_data.get(key, default)
            setattr(self, key, tkinter.BooleanVar(
                self, name=key, value=value))
            c = tkinter.Checkbutton(
                master,
                text=key.replace('_', ' ').title(),
                variable=getattr(self, key),
                anchor='w')
            c.pack(expand=1, fill=tkinter.X)

        # Entries
        for key, name in (('file_location',
                           'Password file location'),
                          ('original_file',
                           'Steganography original file location')):
            setattr(self, key, tkinter.StringVar())
            if initial_data:
                getattr(self, key).set(initial_data.get(key, ''))

            e = LabelEntry(master,
                           width=50,
                           label=name,
                           textvariable=getattr(self, key))
            e.pack()

    def apply(self):
        self.result = {key: getattr(self, key).get() for
                       key in ('sync', 'file_location', 'original_file',
                               'use_steganography', 'clear_on_exit')}


class About(Dialog):
    '''About information and update program button.'''
    def body(self, master, _):
        for name, var in (('', '__summary__'),
                          ('Version: ', '__version__'),
                          ('Author: ', '__author__'),
                          ('Contact: ', '__email__'),
                          ('Licence: ', '__license__'),
                          ('', '__uri__')):
            label = tkinter.Label(master, text=f'{name} {eval(var)}')
            label.pack(fill=tkinter.X, expand=1)

        version = check_version('acid_vault')
        if version != __version__:
            label = tkinter.Label(
                master, text=f'Version on PyPi: {version}')
            label.pack(fill=tkinter.X, expand=1)
            button = tkinter.Button(master,
                                    text='Update (Will restart program)',
                                    command=lambda: self.update(version))
            button.pack()

    def update(self, version):
        '''Update to newest version of program'''
        p = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'install', f'acid_vault=={version}'],
            stdout=subprocess.PIPE)
        p.wait()
        print(str(p.stdout.read(), 'utf-8'))
        path = os.path.join(os.path.dirname(__file__), 'VaultGui.pyw')
        print(f'Starting path: {path}')
        os.execv(sys.executable, [sys.executable, path])

    def buttonbox(self):
        """Standard OK and Cancel buttons."""
        box = tkinter.ttk.Frame(self)

        w = tkinter.ttk.Button(
            box, text="OK", width=10, command=self.ok, default=tkinter.ACTIVE)
        w.pack(side='left', padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()
        return box


class Box(tkinter.Frame):
    """Frame box to make widgets align."""
    def __init__(self, master, widget_type, *args, **kwargs):
        self.master = master
        side = kwargs.pop('side', 'bottom')
        super().__init__(master)
        self.widget = getattr(tkinter, widget_type)(self, *args, **kwargs)
        self.widget.pack(side=side)

    def config(self, *args, **kwargs):
        self.widget.config(*args, **kwargs)


class StatusBar(tkinter.Label):
    '''Status bar widget.'''
    def __init__(self, master, *args, **kwargs):
        self.default_color = master.cget('bg')
        self.master = master
        self._data = kwargs.pop('textvariable', tkinter.StringVar())
        super().__init__(master, *args, textvariable=self._data, **kwargs)

    def set(self, data, color=None):
        color = color or self.default_color
        self._data.set(data)
        self.config(bg=color)
        self.master.update_idletasks()


class LabelEntry(tkinter.Frame):
    '''A labled entry frame.'''
    def __init__(self, master, *args, **kwargs):
        self.master = master
        label = kwargs.pop('label', '')
        super().__init__(master)
        self._label = tkinter.Label(self, text=label)
        self._entry = tkinter.Entry(self, *args, **kwargs)
        self._label.pack(side='top', fill=tkinter.X)
        self._entry.pack(side='top', fill=tkinter.X)

    @property
    def label(self, value):
        self._label.set(value)

    def set_config(self, **kwargs):
        self._entry.configure(**kwargs)

    def focus_set(self, *args, **kwargs):
        self._entry.focus_set(*args, **kwargs)

    def bind(self, *args, **kwargs):
        self._entry.bind(*args, **kwargs)


class Timer():
    """Timer class to triger call back after given time."""
    def __init__(self, master, callback, after, reset_after_trigger=False,
                 *args, **kwargs):
        self.master = master
        self.callback = callback
        self.after = after
        self.args = args
        self.kwargs = kwargs
        self.reset_after_trigger = reset_after_trigger
        self.timer = master.after(self.after, self._trigger)

    def _trigger(self):
        self.callback(*self.args, **self.kwargs)
        if self.reset_after_trigger:
            self.timer = self.master.after(self.after, self._trigger)

    def reset(self, *args, **kwargs):
        """Reset timer"""
        self.timer and self.master.after_cancel(self.timer)
        self.timer = self.master.after(self.after, self._trigger)

    def stop(self):
        """Stop timer."""
        self.timer and self.master.after_cancel(self.timer)

    def start(self):
        """Start timer, only used after it has been stoped."""
        self.timer = self.master.after(self.after, self._trigger)


def check_version(name):
    '''Checks current version for package on pypi'''
    pypi_url = f'https://pypi.org/pypi/{name}/json'
    response = urllib.request.urlopen(pypi_url, timeout=5).read().decode()
    latest_version = max(LooseVersion(s) for s in
                         json.loads(response)['releases'].keys())
    return latest_version
