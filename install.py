import os
import subprocess
import sys
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk

PACKAGE_PATH = 'acid_vault/VaultGUI.pyw'
DESCRIPTION = 'Python Password Vault'
NAME = 'PyVault'
ICON_PATH = False


class Installer():
    def __init__(self, master):
        while True:
            p = subprocess.Popen(['where', 'python'], stdout=subprocess.PIPE)
            output = p.stdout.read().decode(sys.stdin.encoding).split('\n')
            output = [x.strip() for x in output if
                      x and 'WindowsApps' not in x]
            if not output:
                output = self.check_common_places()

            if not output:
                result = tkinter.messagebox.askyesnocancel(
                    'Install Python?',
                    'Python not found on path, install it?\n '
                    'Press No to supply path manually')

                if result:
                    tkinter.messagebox.showwarning(
                        'Add Path', 'Please check "Add to Path" checkbox')
                    basedir = getattr(sys, '_MEIPASS',
                                      os.path.abspath
                                      (os.path.dirname(__file__)))

                    p = subprocess.Popen([os.path.join(basedir,
                                                       'install data',
                                                       'python-3.9.0-amd64.exe')])
                    p.wait()

                    output = self.check_common_places()
                    if not output:
                        tkinter.messagebox.showwarning(
                            'Please restart',
                            'Install will now close, please restart '
                            'installation manually')
                        master.destroy()
                        return

                elif result is None:
                    master.destroy()
                    return
                else:
                    output = tkinter.filedialog.askdirectory()
                    if not output:
                        master.destroy()
                        return
                    output = [output]
                    break

            paths = [os.path.dirname(x) for x in output]
            if len(paths) == 1:
                self.py_path = paths[0]
            else:
                dialog = SelectDistDialog(master, 'Select target', paths)
                if not dialog.result:
                    return
                self.py_path = dialog.result
            break

        python_exec = os.path.join(self.py_path, 'python.exe')
        p = subprocess.Popen(
            [python_exec, '-m', 'pip', 'install', 'acid_vault'])
        p.wait()
        if p.returncode:
            tkinter.messagebox.showerror(
                'Failed to install',
                'Failed to install vault is internet availiable?')
            master.destroy()
            return

        self.create_shortcut()
        master.destroy()

    def create_shortcut(self):
        if not tkinter.messagebox.askyesno(
                'Install Desktop Icon', 'Do you want to add a Desktop Icon?'):
            return
        script_file = os.path.join(
            self.py_path, 'Lib', 'site-packages', PACKAGE_PATH)
        bat_file = os.path.join(
            os.path.dirname(script_file), 'create_shortcut.bat')
        target = f'"{script_file}"'
        with open(bat_file, 'w') as fh:
            print('@echo off', file=fh)
            print('echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs', file=fh)
            print(f'echo sLinkFile = "%userprofile%\Desktop\{NAME}.lnk" >> CreateShortcut.vbs', file=fh)
            print('echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs', file=fh)
            print(f'echo oLink.TargetPath = {target} >> CreateShortcut.vbs', file=fh)
            print(f'echo oLink.WorkingDirectory = "{os.path.dirname(self.py_path)}" >> CreateShortcut.vbs', file=fh)
            print(f'echo oLink.Description = "{DESCRIPTION}" >> CreateShortcut.vbs', file=fh)
            if ICON_PATH:
                print(f'echo oLink.IconLocation = "{ICON_PATH}" >> CreateShortcut.vbs', file=fh)
            print('echo oLink.Save >> CreateShortcut.vbs', file=fh)
            print('cscript CreateShortcut.vbs', file=fh)
            print('del CreateShortcut.vbs', file=fh)
        p = subprocess.Popen([bat_file])
        p.wait()
        os.remove(bat_file)

    def check_common_places(self):
        path_guess = os.path.expanduser(
            os.path.join('~', 'AppData', 'Local', 'Programs', 'Python'))
        try:
            canidates = os.listdir(path_guess)
            return [os.path.join(path_guess, x, 'python.exe') for
                    x in canidates if os.path.exists(
                        os.path.join(path_guess, x, 'python.exe'))]
        except FileNotFoundError:
            return []


class SelectDistDialog(tkinter.Toplevel):
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
        label = tkinter.Label(
            master, text='Please select which Python to install to')
        label.pack(fill=tkinter.X, expand=1)
        for path in initial_data:
            b = tkinter.Button(master,
                               text=path,
                               command=lambda path=path: self.button(path))
            b.pack(fill=tkinter.X, expand=1)

    def buttonbox(self):
        """Standard OK and Cancel buttons."""
        box = tkinter.ttk.Frame(self)

        w = tkinter.ttk.Button(
            box, text="Cancel", width=10, command=self.cancel)
        w.pack(side='left', padx=5, pady=5)

        self.bind("<Escape>", self.cancel)

        box.pack()
        return box

    def button(self, path):
        """On button press."""
        self.withdraw()
        self.update_idletasks()
        self.result = path
        self.cancel()

    def cancel(self, event=None):
        """On Cancel button press."""
        self.parent.focus_set()
        self.destroy()


tk = tkinter.Tk()
Installer(tk)
tk.mainloop()
