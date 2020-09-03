import paramiko
import pickle
import os
import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.ttk

import constants
import ssh
import steganography
from vault import Vault
import widgets

class GUI():
    def __init__(self, master):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.onclose)
        self.vault = None
        self.ssh_config = []
        self.file_config = {}
        
        top = tkinter.Frame(master)
        top.pack(side='top', fill=tkinter.X)
        self.passbox = PasswordBox(master)
        self.passbox.pack(side='top', fill=tkinter.BOTH, expand=1)
        bottom = tkinter.Frame(master)
        bottom.pack(side='top', fill=tkinter.X)

        self.password = tkinter.StringVar()
        password = widgets.LabelEntry(
            top, label='Password', show='*', textvariable=self.password)

        # Buttons
        save_pass = widgets.Box(
            top, 'Button', text='Save passwords', command=self.set_passwords)
        get_pass = widgets.Box(
            top, 'Button', text='Get passwords', command=self.get_passwords)
        setup_files = widgets.Box(
            top, 'Button', text='Setup Files', command=self.setup_files)
        ssh = widgets.Box(
            top, 'Button', text='Setup SSH', command=self.setup_ssh)
        add_pass = tkinter.Button(
            bottom, command=self.add_password, text='Add Password')

        # Checkboxes
        self.do_steganography = tkinter.IntVar()
        stego = widgets.Box(
            top, 'Checkbutton', text='Steganography', variable=self.do_steganography)
        
        # Option menues
        self.file_location = tkinter.StringVar()
        self.file_location.set('Local')
        file_location = tkinter.OptionMenu(
            top, self.file_location, 'Local', 'Remote')
        file_location.configure(width=15)

        # Pack it all up
        password.pack(side='left')
        get_pass.pack(side='left', fill=tkinter.Y)
        save_pass.pack(side='left', fill=tkinter.Y)
        setup_files.pack(side='left', fill=tkinter.Y)
        ssh.pack(side='left', fill=tkinter.Y)
        stego.pack(side='left', fill=tkinter.Y)
        file_location.pack(side='left', fill=tkinter.Y)
        add_pass.pack()
        self.onstart()

    def onclose(self):
        try:
            ssh_config = self.ssh_config
            if ssh_config:
                ssh_config[-1] = ''
            obj = {'attributes': {'ssh_config': ssh_config,
                                  'file_config': self.file_config},
                   'widgets': {'do_steganography': self.do_steganography.get(),
                               'file_location': self.file_location.get()}}
            with open(os.path.join(constants.data_dir(), '.vault'), 'wb') as fh:
                pickle.dump(obj, fh)
        except Exception as err:
            print(err)
        finally:
            self.master.destroy()

    def onstart(self):
        try:
            with open(os.path.join(constants.data_dir(), '.vault'), 'rb') as fh:
                obj = pickle.load(fh)
            for key, value in obj['widgets'].items():
                try:
                    getattr(self, key).set(value)
                except Exception as err:
                    print(err)
            for key, value in obj['attributes'].items():
                setattr(self, key, value)
        except Exception as err:
            print(err)

    def steganography_load(self, fh):
        data = steganography.read(fh, self.file_config['original_file'])
        self.vault = Vault(self.password.get())
        self.vault.load_data(data)

    def steganography_save(self, fh):
        data = self.vault.save_data()
        steganography.write(fh, self.file_config['original_file'], data)

    def get_passwords(self):
        if not self.verify():
            return
        if self.file_location.get() == 'Local':
            self.make_dirs()
            with open(self.file_config['file_location'], 'rb') as fh:
                if self.do_steganography.get():
                    self.steganography_load(fh)
                else:
                    self.vault = Vault(self.password.get(), fh)
        elif self.file_location.get() == 'Remote':
            with ssh.RemoteFile(*self.ssh_config,
                                self.file_config['file_location'],
                                constants.data_dir()) as remote:
                fh = remote.open('rb')
                if not fh:
                    return
                if self.do_steganography.get():
                    self.steganography_load(fh)
                else:
                    self.vault = Vault(self.password.get(), fh)
        else:
            tkinter.messagebox.showerror('Set url/local file',
                                         'URL or Local File has to be set')
            return

        self.passbox.clear()
        self.vault.unlock()
        for password in self.vault.get_objects():
            self.passbox.add(password)

    def set_passwords(self):
        if not self.verify():
            return
        if not self.vault:
            self.vault = Vault(self.password.get())
        objects = [self.passbox.item(x, 'values') for x in
                   self.passbox.get_children()]
        self.vault.set_objects(objects)
        self.vault.lock()
        if self.file_location.get() == 'Local':
            self.make_dirs()
            with open(self.file_config['file_location'], 'wb') as fh:
                if self.do_steganography.get():
                    self.steganography_save(fh)
                else:
                    self.vault.save_file(fh)
        elif self.file_location.get() == 'Remote':
            with ssh.RemoteFile(*self.ssh_config,
                                self.file_config['file_location'],
                                constants.data_dir()) as remote:
                with remote.open('wb') as fh:
                    if self.do_steganography.get():
                        self.steganography_save(fh)
                    else:
                        self.vault.save_file(fh)
        else:
            tkinter.messagebox.showerror(
                'Faulty file location',
                f'File location is unknow {self.file_location.get()}')
        self.vault.unlock()

    def verify(self):
        if not self.password.get():
            tkinter.messagebox.showerror('Set Password',
                                         'Password has to be set')
            return

        if self.file_location.get() == 'Local':
            if not self.file_config['file_location']:
                tkinter.messagebox.showerror('Set Filepath',
                                             'Local Filepath has to be set')
                return
        elif self.file_location.get() == 'Remote':
            # Add validation here
            return True
        else:
            return
        return True

    def setup_files(self):
        result = widgets.SetupFiles(self.master,
                                  'File Config',
                                  self.file_config).result
        if result:
            self.file_config = result

    def add_password(self):
        self.passbox.add()

    def setup_ssh(self):
        result = widgets.SetupSSH(self.master,
                                  'SSH Config',
                                  self.ssh_config).result
        if result:
            self.ssh_config = result

    def make_dirs(self):
        dirname = os.path.dirname(self.file_config['file_location'])
        if dirname:
            os.makedirs(dirname, exsist_ok=True)

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
