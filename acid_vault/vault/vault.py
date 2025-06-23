########################################################################
# Acid Vault                                                           #
#                                                                      #
# This program is free software: you can redistribute it and/or modify #
# it under the terms of the GNU Affero General Public License as       #
# published by the Free Software Foundation, either version 3 of the   #
# License, or (at your option) any later version.                      #
#                                                                      #
# This program is distributed in the hope that it will be useful,      #
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
# GNU Affero General Public License for more details.                  #
#                                                                      #
# You should have received a copy of the GNU Affero General Public     #
# License                                                              #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.#
########################################################################
"""Provides the core functionality for an encrypted password vault.

This module contains the Vault class, which handles the encryption,
decryption, storage, and management of password entries. It supports
different storage backends like local files and remote SSH servers,
and can use steganography to hide the vault data within images.
"""

import ast
import base64
import datetime
import os
import pickle
import random
import string
import uuid

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .helpers import ssh
from .helpers import steganography
from .helpers import version
from .constants import FILE_VERSION, KEEP_DAYS, ITERATIONS
from .constants import UUID, DATE, SYSTEM, USER, PASSWORD, NOTES, DELETED


class VaultError(Exception):
    """Custom exception for vault-related errors."""
    pass


class Vault:
    """Manages passwords, including encryption, decryption, and storage.

    This class is the core of the password vault. It encapsulates the
    password data and provides methods to lock (encrypt) and unlock
    (decrypt)
    the vault. It also handles saving to and loading from different
    storage backends.
    """
    def __init__(self,
                 data_path=None,
                 ssh_params=None,
                 path_to_original=None,
                 update=True,
                 iterations=ITERATIONS):
        """Initialize the Vault.

        Args:
            data_path (str, optional): Path to the vault file.
                Defaults to None.
            ssh_params (dict, optional): Parameters for SSH connection.
                Defaults to None.
            path_to_original (str, optional): Path to the original image
                for steganography. Defaults to None.
            update (bool, optional): Whether to allow updating the vault
                file on the server. Defaults to True.
            iterations (int, optional): Number of iterations for PBKDF2.
                Defaults to ITERATIONS.
        """
        self._locked = False
        # When loaded from local file do not update.
        self.update = update

        if data_path:
            self.load(data_path, ssh_params, path_to_original)
        else:
            self.data = {'salt': os.urandom(16),
                         'iterations': iterations,
                         'vault': [],
                         'timestamp': datetime.datetime.utcnow(),
                         'version': FILE_VERSION}

    @property
    def locked(self):
        """Return the locked status of the vault."""
        return self._locked

    @property
    def timestamp(self):
        """Return the timestamp of the last data modification."""
        return self.data.get('timestamp')

    @property
    def encryption_settings(self):
        """Return the encryption settings."""
        return {'iterations': self.iterations}

    @encryption_settings.setter
    def encryption_settings(self, x):
        """Set the encryption settings."""
        self.iterations = x.get('iterations', self.iterations)

    @property
    def iterations(self):
        """Return the number of iterations for key derivation."""
        return self.data.get('iterations')

    @iterations.setter
    def iterations(self, x):
        """Set the number of iterations for key derivation."""
        self.data['iterations'] = x
        print('iterations set')

    @staticmethod
    def _open(file_path, ssh_params, path_to_original, mode, call):
        """Open a file, either locally or remotely via SSH.

        This is a helper method to abstract away the file opening logic
        for different storage backends.

        Args:
            file_path (str): The path to the file.
            ssh_params (dict): The parameters for the SSH connection.
            path_to_original (str): The path to the original image for
                steganography.
            mode (str): The mode in which to open the file (e.g., 'rb',
                'wb').
            call (function): The function to call with the opened file
                handle.

        Raises:
            VaultError: If the file lock could not be acquired.

        Returns:
            The return value of the `call` function.
        """
        if ssh_params:
            with ssh.RemoteFile(ssh_params, file_path, mode) as fh:
                if not fh:
                    raise VaultError('Could not acquire lock')
                return call(fh, path_to_original)
        else:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, mode) as fh:
                return call(fh, path_to_original)

    @staticmethod
    def force_lock(ssh_params):
        """Force the release of a remote file lock.

        Args:
            ssh_params (dict): The parameters for the SSH connection.
        """
        ssh.force_lock(**ssh_params)

    def update_version(self, password):
        """Update the vault data format to the latest version.

        Args:
            password (str): The master password for the vault.

        Returns:
            bool: True if the vault was updated, False otherwise.
        """
        if not self.update:
            return
        current_version = self.data.get('version')
        if not version.is_greater_version(FILE_VERSION, current_version):
            return
        # Save status of lock, so we know if we should lock again.
        lock_status = self.locked
        if lock_status:
            if not self.unlock(password):
                return

        for index, record in enumerate(self.data['vault']):
            # It has to be magic numbers within this function as the
            # Constant that keeps track of tuple position only reflects
            # last versions order.
            if version.is_greater_version('1.0.0', current_version):
                if isinstance(record, dict):
                    record['date'] = record.get('date', '')
                    record['uid'] = record.get('uid', uuid.uuid4())

            if version.is_greater_version('2.0.0', current_version):
                if isinstance(record, dict):
                    record = [record['uid'],
                              record['date'],
                              record['system'],
                              record['user'],
                              record['password'],
                              record['notes'],
                              '']
                if isinstance(record, (tuple, list)):
                    record = list(record)
                    # Has to be magic numbers here.
                    if isinstance(record[0], str):
                        record[0] = uuid.UUID(record[0])
                    if isinstance(record[1], str) and record[1]:
                        record[1] = datetime.datetime.fromisoformat(record[1])
            self.data['vault'][index] = tuple(record)
        if lock_status:
            self.lock(password)
        return True

    def check_remote(self, file_path, ssh_params, path_to_original):
        """Check the remote vault for updates.

        Compares the timestamp of the local vault with the remote one
        and returns the remote data if it's newer.

        Args:
            file_path (str): The path to the vault file.
            ssh_params (dict): The parameters for the SSH connection.
            path_to_original (str): The path to the original image for
                steganography.

        Raises:
            VaultError: If there is a version mismatch between the local
                and remote vaults.

        Returns:
            dict or None: The remote vault data if it is newer,
                otherwise None.
        """
        def check(fh, path_to_original):
            if path_to_original:
                data = pickle.loads(steganography.read(fh, path_to_original))
            else:
                data = pickle.load(fh)
            remote_ts = data.get('timestamp')
            remote_ver = data.get('version')
            local_ts = self.data.get('timestamp')
            local_ver = self.data.get('version')

            if not (remote_ver and
                    local_ver and
                    version.same_minor_version(remote_ver, local_ver)):
                raise VaultError(
                    f'Version mismatch: {remote_ver=}, {local_ver=}')
            if remote_ts and local_ts and remote_ts > local_ts:
                return data
        return self._open(file_path, ssh_params, path_to_original, 'rb', check)

    def merge(self, password, data, file_path, ssh_params, path_to_original):
        """Merge updates from a remote vault into the local one.

        Args:
            password (str): The master password for the vault.
            data (dict): The remote vault data to merge.
            file_path (str): The path to the vault file.
            ssh_params (dict): The parameters for the SSH connection.
            path_to_original (str): The path to the original image for
                steganography.
        """
        self.unlock(password)
        data = self._unlock(password, data)
        updated = False
        current = {obj[UUID]: obj for obj in self.data['vault']}
        for obj in data:
            obj_id = obj[UUID]
            if obj_id not in current:
                self.add(obj)
                updated = True
            # Checking date.
            elif obj[DATE] > current[obj_id][DATE]:
                self.replace(obj)
                updated = True
        updated = self.remove_deleted() or updated
        self.lock(password)
        if updated:
            self.save(file_path, ssh_params, path_to_original)

    def load(self, file_path, ssh_params=None, path_to_original=None):
        """Load the vault from a file.

        Args:
            file_path (str): The path to the vault file.
            ssh_params (dict, optional): The parameters for the SSH
                connection. Defaults to None.
            path_to_original (str, optional): The path to the original
                image for steganography. Defaults to None.

        Raises:
            VaultError: If the vault file has a newer version than the
                application supports.
        """
        def read(fh, path_to_original):
            if path_to_original:
                data = pickle.loads(
                    steganography.read(fh, path_to_original))
            else:
                data = pickle.load(fh)
            # Loaded data has a version that is higher than program.
            if version.is_greater_version(data['version'], FILE_VERSION):
                raise VaultError(f'Version mismatch: Please update Vault to latest version.')
            else:
                self.data = data
        self._open(file_path, ssh_params, path_to_original, 'rb', read)
        self._locked = True

    def save(self, file_path, ssh_params=None, path_to_original=None):
        """Save the vault to a file.

        Args:
            file_path (str): The path to the vault file.
            ssh_params (dict, optional): The parameters for the SSH
                connection. Defaults to None.
            path_to_original (str, optional): The path to the original
                image for steganography. Defaults to None.
        """
        def write(fh, path_to_original):
            if path_to_original:
                steganography.write(
                    fh, path_to_original, pickle.dumps(self.data))
            else:
                fh.write(pickle.dumps(self.data))
        self.data['timestamp'] = datetime.datetime.utcnow()
        self.data['version'] = FILE_VERSION
        self._open(file_path, ssh_params, path_to_original, 'wb', write)

    def load_clear(self, fh):
        """Load passwords from a clear text file.

        Args:
            fh (file): An open file handle to read from.

        Raises:
            VaultError: If the vault is locked.
        """
        if self.locked:
            raise VaultError('Vault is locked, unlock first!')
        self._locked = False
        for row in fh:
            self.add(ast.literal_eval(row.strip()))

    def save_clear(self, fh):
        """Save passwords to a clear text file.

        Args:
            fh (file): An open file handle to write to.

        Raises:
            VaultError: If the vault is locked.
        """
        if self.locked:
            raise VaultError('Vault is locked, please unlock first')
        for obj in self.data['vault']:
            print(repr(obj), file=fh)

    def lock(self, password):
        """Encrypt and lock the vault using the provided password.

        Args:
            password (str): The master password.
        """
        if self._locked:
            print('Already locked')
            return
        print('Lock:', self.data.get('iterations'))
        data = pickle.dumps(self.data['vault'])
        key = self.create_key(password,
                              self.data['salt'],
                              self.data.get('iterations', ITERATIONS))
        self.data['vault'] = Fernet(key).encrypt(data)
        self._locked = True

    def unlock(self, password):
        """Decrypt and unlock the vault using the provided password.

        Args:
            password (str): The master password.

        Returns:
            dict or None: The unlocked vault data, or None if unlocking
                failed.
        """
        if not self._locked:
            return self.data
        data = self._unlock(password, self.data)
        if data:
            self.data = data
            self._locked = False
        return data

    def _unlock(self, password, data):
        """Helper method to decrypt vault data.

        Args:
            password (str): The master password.
            data (dict): The vault data to decrypt.

        Returns:
            dict or None: The decrypted vault data, or None if
                decryption failed.
        """
        print('Unlock:', data.get('iterations'))
        key = self.create_key(password,
                              data['salt'],
                              data.get('iterations', ITERATIONS))
        try:
            data['vault'] = pickle.loads(Fernet(key).decrypt(data['vault']))
            return data
        except InvalidToken:
            pass

    @staticmethod
    def create_key(password, salt, iterations=ITERATIONS):
        """Generate an encryption key from a password and salt.

        Uses PBKDF2HMAC with SHA256 to derive a key.

        Args:
            password (str): The master password.
            salt (bytes): The salt to use for key derivation.
            iterations (int, optional): The number of iterations.
                Defaults to ITERATIONS.

        Returns:
            bytes: The derived encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
            )
        return base64.urlsafe_b64encode(
            kdf.derive(bytearray(password, 'utf-8')))

    def get_objects(self):
        """Return all password objects from the vault."""
        return self.data['vault']

    def set_objects(self, objs):
        """Replace all password objects in the vault.

        Args:
            objs (list): A list of password objects to set.
        """
        if not self.locked:
            self.data['vault'] = []
            for obj in objs:
                self.add(obj)

    def add(self, obj):
        """Add a new password object to the vault.

        Args:
            obj (tuple): The password object to add.
        """
        self.data['vault'].append(obj)
        self.data['timestamp'] = datetime.datetime.utcnow()

    def replace(self, obj):
        """Replace an existing password object in the vault.

        Args:
            obj (tuple): The password object to replace.

        Returns:
            bool: True if the object was replaced, False otherwise.
        """
        for index, current_obj in enumerate(self.data['vault']):
            if current_obj['uid'] == obj['uid']:
                self.data['vault'][index] = obj
                self.data['timestamp'] = datetime.datetime.utcnow()
                return True

    def remove_password(self, obj):
        """Remove a specific password object from the vault.

        Args:
            obj (tuple): The password object to remove.
        """
        self.data['vault'].remove(obj)

    def remove_deleted(self):
        """Permanently remove password objects marked as deleted.

        Objects are removed if they have been marked as deleted for
        more than KEEP_DAYS.

        Returns:
            bool: True if any objects were removed, False otherwise.
        """
        now = datetime.datetime.now()
        keep = datetime.timedelta(days=KEEP_DAYS)
        before = len(self.data['vault'])
        self.data['vault'] = [record for record in self.data['vault']
                              if not (record[DELETED] and
                                      record[DATE] + keep < now)
                              ]
        return not before == len(self.data['vault'])


def generate_password(password_type='alpha', n=10):
    """Password generator to suggest randomized passwords."""
    alphabets = {'alpha': (string.ascii_letters, 'isupper', 'islower'),
                 'alphanum': (string.ascii_letters + string.digits,
                              'isupper', 'islower', 'isdigit'),
                 'alphanumspecial': (string.ascii_letters + string.digits + '!"#¤%&/()=?',
                                     'isupper', 'islower', 'isdigit'),
                 'mobilealpha': (string.ascii_lowercase, 'islower'),
                 'mobilealphanum': (string.ascii_lowercase, 'islower'),
                 'mobilealphanumspecial': (string.ascii_lowercase, 'islower'),
                 'numerical': (string.digits, 'isdigit')}
    if password_type not in alphabets:
        raise KeyError('Password type has to be one of the following:'
                       f' {", ".join(alphabets.keys())} it is'
                       f' "{password_type}".')
    while True:
        alphabet = alphabets[password_type][0]
        password = random.choices(alphabet, k=n)
        if password_type.startswith('mobile'):
            password[0] = password[0].upper()
        if 'mobilealphanum' in password_type:
            password[-2] = random.choice(string.digits)
        if password_type == 'mobilealphanumspecial':
            password[-1] = random.choice('!"#¤%&/()=?')

        for test in alphabets[password_type][1:]:
            if not [c for c in password if getattr(c, test)()]:
                break
        else:
            if password_type == 'alphanumspecial':
                if not [c for c in password if not c.isalpha()]:
                    continue
            break
    return ''.join(password)
