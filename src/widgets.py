import tkinter

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
                           label=key.title(),
                           textvariable=getattr(self, key))
            e.pack()
            if initial_data:
                getattr(self, key).set(initial_data[index])
                
        
    def apply(self):
        """Set result upon OK button press."""
        self.result = (self.system.get(),
                       self.username.get(),
                       self.password.get(),
                       self.notes.get())

class ButtonBox(tkinter.Frame):
    def __init__(self, master, *args, **kwargs):
        self.master = master
        side = kwargs.pop('side', 'bottom')
        super().__init__(master)
        self.button = tkinter.Button(self, *args, **kwargs)
        self.button.pack(side=side)

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
