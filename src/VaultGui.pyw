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
    """GUI to handle a password vault."""
    def __init__(self, master):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.onclose)
        self.title = 'PyVault'
        self.master.title(self.title)
        self.vault = None
        self.ssh_config = []
        self.file_config = {}
        
        top = tkinter.Frame(master)
        top.pack(side='top', fill=tkinter.X)
        self.passbox = PasswordBox(master)
        self.passbox.dirty.trace('w', self.dirty)
        self.passbox.pack(side='top', fill=tkinter.BOTH, expand=1)
        self.status = widgets.StatusBar(master, relief=tkinter.RAISED)
        self.status.pack(side='top', fill=tkinter.X)
        bottom = tkinter.Frame(master)
        bottom.pack(side='top', fill=tkinter.X)

        self.password = tkinter.StringVar()
        self._password = None
        password = widgets.LabelEntry(top,
                                      label='Password',
                                      show='*',
                                      textvariable=self.password)

        password.bind('<Return>', self.on_return_key)
        timer = Timer(self.master, self.lock, 5000*60)
        master.bind_all('<Any-KeyPress>', timer.reset)
        master.bind_all('<Any-ButtonPress>', timer.reset)

        # Buttons
        save_pass = widgets.Box(
            top, 'Button', text='Save passwords', command=self.set_passwords)
        get_pass = widgets.Box(
            top, 'Button', text='Get passwords', command=self.get_passwords)
        self.lock_btn = widgets.Box(
            top, 'Button', text='Unlock', command=self.toggle_lock, state=tkinter.DISABLED)
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
        self.lock_btn.pack(side='left', fill=tkinter.Y)
        setup_files.pack(side='left', fill=tkinter.Y)
        ssh.pack(side='left', fill=tkinter.Y)
        stego.pack(side='left', fill=tkinter.Y)
        file_location.pack(side='left', fill=tkinter.Y)
        add_pass.pack()
        self.onstart()
        password.focus_set()
        self.status.set('Init OK')
        
    def onclose(self):
        """Runs on GUI close to save settings."""
        if self.dirty() and not tkinter.messagebox.askokcancel(
            'Quit without save?', 'Unsaved passwords exists, quit anyway?'):
            return
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
        """Runs on GUI start to load saved settings."""
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

    def on_return_key(self, *event):
        if self.vault and self.vault.locked:
            self.update_password_box()
        else:
            self.get_passwords()

    def steganography_load(self, fh):
        """Load hidden data from a file."""
        data = steganography.read(fh, self.file_config['original_file'])
        self.vault = Vault()
        self.vault.load_data(data)

    def steganography_save(self, fh):
        """Save data hidden in a file."""
        data = self.vault.save_data()
        steganography.write(fh, self.file_config['original_file'], data)

    def get_passwords(self, *args):
        """Get and unlock passwords from vault."""
        if not self.verify():
            return
        self.status.set('Getting passwords')
        if self.file_location.get() == 'Local':
            self.make_dirs()
            with open(self.file_config['file_location'], 'rb') as fh:
                if self.do_steganography.get():
                    self.steganography_load(fh)
                else:
                    self.vault = Vault(fh)
        elif self.file_location.get() == 'Remote':
            try:
                with ssh.RemoteFile(*self.ssh_config,
                                    self.file_config['file_location'],
                                    constants.data_dir()) as remote:
                    fh = remote.open('rb')
                    if not fh:
                        return
                    if self.do_steganography.get():
                        self.steganography_load(fh)
                    else:
                        self.vault = Vault(fh)
            except Exception as err:
                self.status.set(err, color='red')
                return
        else:
            tkinter.messagebox.showerror('Set url/local file',
                                         'URL or Local File has to be set')
            return
        self.status.set('Passwords successfully recieved')
        self.update_password_box()

    def update_password_box(self):
        """Load passwords in to GUI."""
        self.status.set('Updating password box')
        self.passbox.clear()
        self._password = self.password.get()
        self.status.set('Unlocking vault')
        self.vault.unlock(self._password)
        self.lock_btn.config(text='Lock')
        self.lock_btn.config(state=tkinter.NORMAL)
        for password in sorted(self.vault.get_objects()):
            self.passbox.add(password)
        self.passbox.dirty.set(False)
        self.status.set('Passwords updated')

    def set_passwords(self):
        """Save password in to file."""
        self.status.set('Saving passwords')
        if not self.verify():
            return
        if not self.vault:
            self.vault = Vault(self.password.get())
        objects = [self.passbox.item(x, 'values') for x in
                   self.passbox.get_children()]
        self.vault.set_objects(objects)
        self.vault.lock(self._password)
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
        self.vault.unlock(self._password)
        self.passbox.dirty.set(False)
        self.status.set('Passwords saved')

    def verify(self):
        """Verify mandatory information."""
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
        """Setup files throught dialog."""
        result = widgets.SetupFiles(self.master,
                                  'File Config',
                                  self.file_config).result
        if result:
            self.file_config = result

    def add_password(self):
        """Add a new password to password list."""
        self.passbox.add()

    def setup_ssh(self):
        """Setup ssh settings throught a dialog."""
        result = widgets.SetupSSH(self.master,
                                  'SSH Config',
                                  self.ssh_config).result
        if result:
            self.ssh_config = result

    def make_dirs(self):
        """Create directory to contain files if it does not exist."""
        dirname = os.path.dirname(self.file_config['file_location'])
        if dirname:
            os.makedirs(dirname, exsist_ok=True)

    def lock(self):
        """Lock vault, and clear local password list."""
        self.status.set('Locking vault')
        if self.vault and not self.vault.locked:
            self.vault.lock(self._password)
            self.lock_btn.config(text='Unlock')
        self._password = None
        self.password.set('')
        self.passbox.clear()
        self.status.set('Vault locked')
    def toggle_lock(self):
        """Toggle lock and unlock of vault."""
        if self.password.get() and self.vault and self.vault.locked:
            self.update_password_box()          
        elif self.vault and self._password:
            self.lock()

    def dirty(self, *args, **kwargs):
        dirty = ' *' if self.passbox.dirty.get() else ''
        self.master.title(self.title + dirty)
        return bool(dirty)


class PasswordBox(tkinter.ttk.Treeview):
    """Class to display password list."""
    def __init__(self, master):
        columns = ('System', 'User Name', 'Password', 'Notes')
        super().__init__(master,
                         columns=columns,
                         displaycolumns=('System', 'User Name'),
                         show='headings')
        for name in columns:
            self.heading(name, text=name)
        self.bind('<ButtonPress-1>', self.on_click)
        self.dirty = tkinter.BooleanVar()
        self.dirty.set(False)

    def clear(self):
        """Remove all unlocked passwords from the list."""
        children = self.get_children()
        self.dirty.set(False)
        if children:
            self.delete(*children)

    def add(self, password=None):
        """Add new password to password list."""
        password = password or widgets.AddPassword(self.master).result
        if not password:
            return
        for index, iid in enumerate(self.get_children()):
            if self.set(iid, 'System').lower() > password[0].lower():
                self.insert('', index, values=password)
                break
        else:
            self.insert('', 'end', values=password)
        self.dirty.set(True)

    def edit(self, iid):
        """Edit password."""
        values = self.item(iid, 'values')
        result = widgets.AddPassword(self.master, 'Password', values).result
        # We got a result and atleast one field has changed
        if result and [x for x in zip(values, result) if x[0] != x[1]]:
            self.delete(iid)
            self.add(result)
        
    def on_click(self, event):
        """Open Edit dialog on click."""
        region = self.identify("region", event.x, event.y)
        if region == 'heading':
            return
        self.edit(self.identify_row(event.y))

class Timer():
    """Timer class to triger call back after given time."""
    def __init__(self, master, callback, after):
        self.master = master
        self.callback = callback
        self.after = after
        self.timer = master.after(after, callback)

    def reset(self, *args, **kwargs):
        """Reset timer"""
        self.timer and self.master.after_cancel(self.timer)
        self.timer = self.master.after(self.after, self.callback)
 
tk = tkinter.Tk()
GUI(tk)
tk.mainloop()
