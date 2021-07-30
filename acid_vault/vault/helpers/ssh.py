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
import tempfile
import tkinter.messagebox

from . import constants

LOCK_PATH = r'.lock/vault.lock'


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
    def __init__(self, ssh_params, filepath, *args, **kwargs):
        host, port, username, password = [ssh_params.get(x) for x in
                                          ('host',
                                           'port',
                                           'username',
                                           'password')]
        self.safe_write = None
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(RejectKeyPolicy())
        self.known_hosts = os.path.join(constants.data_dir(), '.know_hosts')
        try:
            self.ssh.load_host_keys(self.known_hosts)
        except FileNotFoundError:
            os.makedirs(constants.data_dir(), exist_ok=True)
            with open(self.known_hosts, 'w'):
                pass
            self.ssh.load_host_keys(self.known_hosts)
        self._connect(host, port, username, password)
        self.filepath = filepath
        self.sftp = None
        self.stat = None
        self.lock = None
        self.lock_script_path = '/tmp/lock_script.cmd'
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
        if self.safe_write:
            self.ssh.exec_command(f'mv {self.filepath}.bak {self.filepath}')
        if self.stat:
            self.sftp.utime(self.filepath, (self.stat.st_atime,
                                            self.stat.st_mtime))
        for con in ('fh', 'sftp', 'ssh'):
            try:
                getattr(self, con).close()
            except Exception:
                pass
        if self.lock:
            try:
                self.lock.write('quit')
            except Exception as error:
                print(f'Failed to close lock: {error}')

    def _open(self, mode='r', *args, timeout=15, **kwargs):
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
        if [x for x in args if 'w' in x] or 'w' in kwargs.get('mode', ''):
            options = f'-e -w {timeout}'
        else:
            options = f'-s -w {timeout}'
        self.lock = self.aquire_lock(options)
        if not self.lock:
            print('Failed to aquire lock')
            return
        if 'w' in mode and self.filepath == path:
            self.safe_write = True
            path = f'{path}.bak'
        return self.sftp.open(path, *args, mode=mode, **kwargs)

    def create_lock_script(self):
        try:
            self.sftp.stat(self.lock_script_path)
        except (IOError, FileNotFoundError):
            fh, file_path = tempfile.mkstemp(text=True)
            with self.sftp.open(self.lock_script_path, 'w') as fh:
                print('#!/bin/sh\n'
                      'echo "OK"\n'
                      'INPUT=init\n'
                      'while [ "$INPUT" != "quit" ]\n'
                      '    do\n'
                      '        read INPUT\n'
                      '    done\n',
                      file=fh)
            self.ssh.exec_command(f'chmod +x {self.lock_script_path}')

    def aquire_lock(self, options='-e -w 15'):
        self.create_lock_script()
        self.ssh.exec_command(
            f'mkdir -p {os.path.dirname(LOCK_PATH)}')
        stdin, stdout, stderr = self.ssh.exec_command(
            f'flock {options} {LOCK_PATH} -c {self.lock_script_path}')
        if stdout.readline():
            return stdin

    def release_lock(self, pipe):
        pipe.write('quit')


def force_lock(host, port, user, password=None):
    client = paramiko.SSHClient()
    client.connect(host, int(port), user, password)
    client.exec_command(f'rm {LOCK_PATH}')
    client.close()


def load_host_keys(client):
    data_dir = constants.data_dir()
    try:
        client.load_host_keys(os.path.join(data_dir, '.know_hosts'))
    except FileNotFoundError:
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, '.know_hosts'), 'w'):
            pass


def upload_pub_key(
        host, port, user, password, key_path, accept_unknown_host=False,
        comment=False):
    client = paramiko.SSHClient()
    if accept_unknown_host:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    client.connect(host, int(port), user, password)
    transport = client.get_transport()
    transport.send_ignore()
    sftp = client.open_sftp()
    key = read_key(key_path)
    try:
        sftp.mkdir('.ssh')
    except IOError:
        pass
    with sftp.open('.ssh/authorized_keys', 'r+') as fh:
        existing_keys = [x.rstrip('\n') for x in fh.readlines()]
        if key in existing_keys:
            return
        if comment:
            print(f'# {comment}', file=fh)
        print(key, file=fh)
    sftp.close()
    transport.close()
    client.close()


def read_key(key_path):
    with open(key_path) as fh:
        rows = [x.strip('\n') for x in fh.readlines()]
        comment = rows[1].split('"')[1]
        key = ''.join(rows[2:-1])
        return f'ssh-rsa {key} {comment}'


class RejectKeyPolicy(paramiko.client.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        raise MissingKeyError(client, hostname, key)
