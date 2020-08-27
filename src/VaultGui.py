import pickle
import platform
import os
import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.ttk

from vault import Vault
import widgets

class GUI():
    def __init__(self, master):
        self.master = master
        #self.master.protocol("WM_DELETE_WINDOW", self.onclose)
        self.vault = None
        
        top = tkinter.Frame(master)
        top.pack(side='top', fill=tkinter.X)
        self.passbox = PasswordBox(master)
        self.passbox.pack(side='top', fill=tkinter.BOTH, expand=1)
        bottom = tkinter.Frame(master)
        bottom.pack(side='top', fill=tkinter.X)

        self.password = tkinter.StringVar()
        password = widgets.LabelEntry(
            top, label='Password', show='*', textvariable=self.password)
        
        self.ssh_password = tkinter.StringVar()
        ssh_password = widgets.LabelEntry(
            top, label='SSH Password', show='*', textvariable=self.ssh_password)
        
        self.url = tkinter.StringVar()
        url = widgets.LabelEntry(top, label='URL', textvariable=self.url)


        self.local_file = tkinter.StringVar()
        local_file = widgets.LabelEntry(
            top, label='Local File', textvariable=self.local_file)

        save_pass = widgets.ButtonBox(
            top, text='Save passwords', command=self.set_passwords)
        get_pass = widgets.ButtonBox(
            top, text='Get passwords', command=self.get_passwords)
        get_file = widgets.ButtonBox(
            top, text='Get file', command=self.get_file)
        add_pass = tkinter.Button(
            bottom, command=self.add_password, text='Add Password')
        add_pass.pack()

        password.pack(side='left')
        ssh_password.pack(side='left')
        url.pack(side='left')
        local_file.pack(side='left')
        get_file.pack(side='left', fill=tkinter.Y)
        get_pass.pack(side='left', fill=tkinter.Y)
        save_pass.pack(side='left', fill=tkinter.Y)

    @property
    def data_dir(self):
        system = platform.system()
        if system == 'Windows':
            path = os.path.join('appdata', 'local', 'vault')
        elif system == 'Linux':
            path = '.vault'
        else:
            path = ''
        path = os.path.expanduser(os.path.join('~', path))
        os.makedirs(path, exist_ok=True)
        return path
        
    def get_passwords(self):
        if not self.verify():
            return

        if self.local_file.get():
            with open(self.local_file.get(), 'rb') as fh:
                self.vault = Vault(self.password.get(), fh)
        elif self.url.get():
            pass
        else:
            tkinter.messagebox.showerror('Set url/local file', 'URL or Local File has to be set')

        self.passbox.clear()
        for password in self.vault.get_objects():
            self.passbox.add(password)

    def set_passwords(self):
        if not self.verify():
            return
        if not self.vault:
            self.vault = Vault(self.password.get())
            self.vault.create_key()
        objects = [self.passbox.item(x, 'values') for x in self.passbox.get_children()]
        self.vault.set_objects(objects)
        local_file = self.local_file.get()
        if local_file:
            with open(local_file, 'wb') as fh:
                self.vault.write(fh)
        elif url:
            pass

    def verify(self):
        if not self.password.get():
            tkinter.messagebox.showerror('Set Password',
                                         'Password has to be set')
            return
        
        if self.url.get() and self.local_file.get():
            tkinter.messagebox.showerror(
                'Only one can be set',
                'URL and Local File cannot be set at the same time')
            return
        return True

    def get_file(self):
        path = tkinter.filedialog.asksaveasfilename(initialdir=self.data_dir)
        if path:
            self.local_file.set(path)

    def add_password(self):
        self.passbox.add()

class PasswordBox(tkinter.ttk.Treeview):
    def __init__(self, master):
        columns = ('System', 'User Name', 'Password', 'Notes')
        super().__init__(master,
                         columns=columns,
                         displaycolumns=('System', 'User Name'),
                         show='headings')
        for name in columns:
            self.heading(name, text=name)
        self.bind('<ButtonPress-1>', self.on_click)

    def clear(self):
        children = self.get_children()
        if children:
            self.delete(children)

    def add(self, password=None):
        password = password or widgets.AddPassword(self.master).result
        if not password:
            return
        for index, iid in enumerate(self.get_children()):
            if self.set(iid, 'System') > password[0]:
                self.insert('', index, values=password)
                break
        else:
            self.insert('', 'end', values=password)

    def edit(self, iid):
        values = self.item(iid, 'values')
        result = widgets.AddPassword(self.master, 'Password', values).result
        if result and [x for x in zip(values, result) if x[0] != x[1]]:
            self.delete(iid)
            self.add(result)
        
    def on_click(self, event):
        region = self.identify("region", event.x, event.y)
        if region == 'heading':
            return
        self.edit(self.identify_row(event.y))
        
tk = tkinter.Tk()
GUI(tk)
tk.mainloop()
