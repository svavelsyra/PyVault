import paramiko
import pickle
import platform
import os
import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.ttk

import ssh
from vault import Vault
import widgets

class GUI():
    def __init__(self, master):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.onclose)
        self.vault = None
        self.ssh_config = ['', '', '', '', '']
        
        top = tkinter.Frame(master)
        top.pack(side='top', fill=tkinter.X)
        self.passbox = PasswordBox(master)
        self.passbox.pack(side='top', fill=tkinter.BOTH, expand=1)
        bottom = tkinter.Frame(master)
        bottom.pack(side='top', fill=tkinter.X)

        self.password = tkinter.StringVar()
        password = widgets.LabelEntry(
            top, label='Password', show='*', textvariable=self.password)

        self.local_file = tkinter.StringVar()
        local_file = widgets.LabelEntry(
            top, label='Local File', textvariable=self.local_file)

        save_pass = widgets.Box(
            top, 'Button', text='Save passwords', command=self.set_passwords)
        get_pass = widgets.Box(
            top, 'Button', text='Get passwords', command=self.get_passwords)
        get_file = widgets.Box(
            top, 'Button', text='Get file', command=self.get_file)
        ssh = widgets.Box(
            top, 'Button', text='Setup SSH', command=self.setup_ssh)
        add_pass = tkinter.Button(
            bottom, command=self.add_password, text='Add Password')

        self.file_location = tkinter.StringVar()
        self.file_location.set('Local')
        file_location = tkinter.OptionMenu(
            top, self.file_location, 'Local', 'Remote')
        file_location.configure(width=15)
        
        password.pack(side='left')
        local_file.pack(side='left')
        get_file.pack(side='left', fill=tkinter.Y)
        get_pass.pack(side='left', fill=tkinter.Y)
        save_pass.pack(side='left', fill=tkinter.Y)
        ssh.pack(side='left', fill=tkinter.Y)
        file_location.pack(side='left', fill=tkinter.Y)
        add_pass.pack()
        self.onstart()

    def onclose(self):
        try:
            obj = {'values' : {key: getattr(self, key).get() for key in ('local_file', 'file_location')}}
            ssh_config = self.ssh_config or ['', '', '', '', '']
            ssh_config[-1] = ''
            obj['ssh'] = ssh_config
            with open(os.path.join(self.data_dir, '.vault'), 'wb') as fh:
                pickle.dump(obj, fh)
        except Exception as err:
            print(err)
        finally:
            self.master.destroy()

    def onstart(self):
        try:
            with open(os.path.join(self.data_dir, '.vault'), 'rb') as fh:
                obj = pickle.load(fh)
            for key, value in obj['values'].items():
                getattr(self, key).set(value)
            self.ssh_config = obj['ssh']
        except Exception as err:
            print(err)

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
        if self.file_location.get() == 'Local':
            with open(self.local_file.get(), 'rb') as fh:
                self.vault = Vault(self.password.get(), fh)
        elif self.file_location.get() == 'Remote':
            with ssh.RemoteFile(*self.ssh_config, self.data_dir) as remote:
                fh = remote.open('rb')
                if not fh:
                    return
                self.vault = Vault(self.password.get(), fh)
        else:
            tkinter.messagebox.showerror('Set url/local file',
                                         'URL or Local File has to be set')

        self.passbox.clear()
        for password in self.vault.get_objects():
            self.passbox.add(password)

    def set_passwords(self):
        if not self.verify():
            return
        if not self.vault:
            self.vault = Vault(self.password.get())
            self.vault.create_key()
        objects = [self.passbox.item(x, 'values') for x in
                   self.passbox.get_children()]
        self.vault.set_objects(objects)
        if self.file_location.get() == 'Local':
            with open(self.local_file.get(), 'wb') as fh:
                self.vault.write(fh)
        elif self.file_location.get() == 'Remote':
            with ssh.RemoteFile(*self.ssh_config, self.data_dir) as remote:
                self.vault.write(remote.open('wb'))
        else:
            tkinter.messagebox.showerror(
                'Faulty file location',
                f'File location is unknow {self.file_location.get()}')

    def verify(self):
        if not self.password.get():
            tkinter.messagebox.showerror('Set Password',
                                         'Password has to be set')
            return
        if self.file_location.get() == 'Local' and not self.local_file.get():
            tkinter.messagebox.showerror('Set Local filepath',
                                         'Local filepath has to be set')
            return
        elif self.file_location.get() == 'Remote':
            # Add validation here
            return True
        else:
            return
        return True

    def get_file(self):
        path = tkinter.filedialog.asksaveasfilename(initialdir=self.data_dir)
        if path:
            self.local_file.set(path)

    def add_password(self):
        self.passbox.add()

    def setup_ssh(self):
        result = widgets.SetupSSH(self.master,
                                  'SSH Config',
                                  self.ssh_config).result
        if result:
            self.ssh_config = result

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
