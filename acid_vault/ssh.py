###############################################################################
# Acid Vault                                                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

'''
Handle files on Remote server through ssh.
Wrapper around Paramiko sftp server.
'''
import os
import paramiko
import tkinter.messagebox

import constants


class RemoteFile():
    """
    Class to handle remote files through ssh.
    Implements context manager.
    """
    def __init__(self, ssh_params, filepath, *args, **kwargs):
        host, port, username, password = [ssh_params.get(x) for x in
                                          ('host',
                                           'port',
                                           'username',
                                           'password')]
        self.ssh = paramiko.SSHClient()
        data_dir = constants.data_dir()
        try:
            self.ssh.load_host_keys(os.path.join(data_dir, '.know_hosts'))
        except FileNotFoundError:
            os.makedirs(data_dir, exist_ok=True)
            with open(os.path.join(data_dir, '.know_hosts'), 'w'):
                pass
        self._connect(host, port, username, password)
        self.filepath = filepath
        self.sftp = None
        self.stat = None
        self.fh = self._open(*args, **kwargs)

    def __enter__(self):
        return self.fh

    def __exit__(self, *args):
        self.close()

    def _connect(self, host, port, username, password, unknown_host=False):
        try:
            if unknown_host:
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            self.ssh.connect(host, int(port), username, password)
        except paramiko.ssh_exception.SSHException as err:
            if str(err) == 'Authentication failed.':
                tkinter.messagebox.showerror('Authentication failed.',
                                             'Authentication failed.')
                self.ssh.close()
                return
            if tkinter.messagebox.askokcancel(
                    "Unknown host", "Unknown host!\n"
                    "Do you want to continue connecting?"):
                self._connect(host, port, username, password, True)
            else:
                self.ssh.close()

    def _makedirs(self, path):
        current_path = ''
        for p in path.split('/'):
            current_path = (current_path and f'{current_path}/{p}') or p
            try:
                self.sftp.stat(current_path)
            except FileNotFoundError:
                self.sftp.mkdir(current_path)

    def close(self):
        '''Close all open handles in the correct order.'''
        if self.stat:
            self.sftp.utime(self.filepath, (self.stat.st_atime,
                                            self.stat.st_mtime))
        for con in ('fh', 'sftp', 'ssh'):
            try:
                getattr(self, con).close()
            except Exception:
                pass

    def _open(self, *args, **kwargs):
        """Open remote path."""
        path = kwargs.pop('path', self.filepath)
        transport = self.ssh.get_transport()
        try:
            transport.send_ignore()
        except Exception:
            return
        self.sftp = self.ssh.open_sftp()
        self._makedirs(os.path.dirname(path))
        try:
            self.stat = self.sftp.stat(path)
        except FileNotFoundError:
            pass
        return self.sftp.open(path, *args, **kwargs)
