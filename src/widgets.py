import tkinter

from vault import generate_password
from vault import VALID_PASSWORD_TYPES

class Dialog(tkinter.Toplevel):
    """
    Parent Dialog frame, inherit and override
    boddy and apply methods.
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

class AddPassword(Dialog):
    def body(self, master, initial_data):
        """Body of set key dialog."""
        for index, key in enumerate(('system',
                                     'username',
                                     'password',
                                     'notes')):
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
        length = tkinter.OptionMenu(f, pw_len, *range(4,16))
        length.configure(width=2)
        
        gen_pass.pack(side='left')
        length.pack(side='left')
        b = tkinter.Button(
            f,
            text='Generate Password',
            command=lambda:self.password.set(
                generate_password(
                    pw_type.get(), pw_len.get())))
        b.pack(side='left')
                
        
    def apply(self):
        """Set result upon OK button press."""
        self.result = (self.system.get(),
                       self.username.get(),
                       self.password.get(),
                       self.notes.get())
        

class SetupSSH(Dialog):
    def body(self, master, initial_data):
        """Body of set key dialog."""
        for index, key in enumerate(('host',
                                     'port',
                                     'username',
                                     'password')):
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
                    getattr(self, key).set(initial_data[index])
                except IndexError:
                    pass
        
    def apply(self):
        """Set result upon OK button press."""
        self.result = [getattr(self, key).get() for
                       key in ('host', 'port', 'username', 'password')]

class SetupFiles(Dialog):
    def body(self, master, initial_data):
        for key in ('file_location', 'original_file'):
            setattr(self, key, tkinter.StringVar())
            e = LabelEntry(master,
                           width=50,
                           label=key.title().replace('_', ' '),
                           textvariable=getattr(self, key))
            e.pack()
            if initial_data:
                getattr(self, key).set(initial_data.get(key, ''))

    def apply(self):
        self.result = {key: getattr(self, key).get() for
                       key in ('file_location', 'original_file')}

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


class LabelEntry(tkinter.Frame):
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
