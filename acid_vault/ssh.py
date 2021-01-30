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
"""
Handle files on Remote server through ssh.
Wrapper around Paramiko sftp server.
"""
import os
import paramiko
import tkinter.messagebox


class MissingKeyError(Exception):
    def __init__(self, client, hostname, key):
        super().__init__(f'{hostname}: {key.get_base64()} '
                         'is missing in hostfile')
        self.client = client
        self.hostname = hostname
        self.key = key


class RemoteFile():
    """
    Class to handle remote files through ssh.
    Implements context manager.
    """
    def __init__(self, ssh_params, filepath, data_dir, *args, **kwargs):
        host, port, username, password = [ssh_params[x] for x in
                                          ('host',
                                           'port',
                                           'username',
                                           'password')]
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(RejectKeyPolicy())
        self.known_hosts = os.path.join(data_dir, '.know_hosts')
        try:
            self.ssh.load_host_keys(self.known_hosts)
        except FileNotFoundError:
            os.makedirs(data_dir, exist_ok=True)
            with open(self.known_hosts, 'w'):
                pass
            self.ssh.load_host_keys(self.known_hosts)
        self._connect(host, port, username, password)
        self.filepath = filepath
        self.sftp = None
        self.stat = None
        self.fh = self._open(*args, **kwargs)

    def __enter__(self):
        return self.fh

    def __exit__(self, *args):
        self.close()

    def _connect(self, host, port, username, password):
        try:
            self.ssh.connect(host, int(port), username, password)
        except paramiko.ssh_exception.BadHostKeyException as err:
            if tkinter.messagebox.askokcancel(
                    'Bad Host Key',
                    f'{err}\n '
                    'This may be a Man In the Middle attack\n '
                    'Continue anyway?'):
                keys = self.ssh.get_host_keys()
                hostname = (err.hostname if err.hostname in keys else
                            f'[{err.hostname}]:{port}')
                if hostname not in keys:
                    raise
                self.add_key(hostname, err.key)
                self._connect(host, port, username, password)
                return

        except paramiko.ssh_exception.SSHException as err:
            if str(err) == 'Authentication failed.':
                tkinter.messagebox.showerror('Authentication failed.',
                                             'Authentication failed.')
        except MissingKeyError as err:
            if tkinter.messagebox.askokcancel(
                    'Missing Host Key',
                    f'{err}\n '
                    'Continue anyway?'):
                self.add_key(err.hostname, err.key)
                self._connect(host, port, username, password)
                return
        else:
            # All OK
            return
        # If we have here an exception has happened
        self.ssh.close()

    def add_key(self, hostname, key):
        """Adds keys to host file."""
        keys = self.ssh.get_host_keys()
        keys.pop(hostname, '')
        keys.add(hostname, 'ssh-rsa', key)
        keys.save(self.known_hosts)

    def _makedirs(self, path):
        current_path = ''
        for p in path.split('/'):
            current_path = (current_path and f'{current_path}/{p}') or p
            try:
                self.sftp.stat(current_path)
            except FileNotFoundError:
                self.sftp.mkdir(current_path)

    def close(self):
        """Close all open handles in the correct order."""
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
            return self.sftp.open(path, *args, **kwargs)
        except FileNotFoundError:
            tkinter.messagebox.showerror(
                'File not found!', f'Unable to find the file {self.filepath}')


class RejectKeyPolicy(paramiko.client.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        raise MissingKeyError(client, hostname, key)
