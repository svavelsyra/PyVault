import pickle
import tkinter

from vault import Vault
from password import Password

class GUI():
    def __init__(self, master):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.onclose)
        self.onstart()

    def onstart(self):
        try:
            with open('vault.dat', 'rb') as fh:
                pass
        except FileNotFoundError:
            pass

    def onclose(self):
        try:
            with open('vault.dat', 'wb') as fh:
                pass
        finally:
            self.master.destroy()
            
tk = tkinter.Tk()
GUI(tk)
tk.mainloop()
