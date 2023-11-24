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
"""Encrypts and decrypts data."""
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
from .constants import VERSION, KEEP_DAYS
from .constants import UUID, DATE, SYSTEM, USER, PASSWORD, NOTES, DELETED


class VaultError(Exception):
    """Vault related errors."""
    pass


class Vault:
    """Class to hold salt, iterations and the data."""
    def __init__(self,
                 data_path=None,
                 ssh_params=None,
                 path_to_original=None,
                 update=True):
        self._locked = False
        # When loaded from local file do not update.
        self.update = update

        if data_path:
            self.load(data_path, ssh_params, path_to_original)
        else:
            self.data = {'salt': os.urandom(16),
                         'iterations': 1000000,
                         'vault': [],
                         'timestamp': datetime.datetime.utcnow(),
                         'version': VERSION}

    @property
    def locked(self):
        """Locked status of the vault"""
        return self._locked

    @property
    def timestamp(self):
        return self.data.get('timestamp')

    def _open(self, file_path, ssh_params, path_to_original, mode, call):
        if ssh_params:
            with ssh.RemoteFile(ssh_params, file_path, mode) as fh:
                if not fh:
                    raise VaultError('Could not acquire lock')
                return call(fh, path_to_original)
        else:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, mode) as fh:
                return call(fh, path_to_original)

    def force_lock(self, ssh_params):
        ssh.force_lock(**ssh_params)

    def update_version(self, password):
        if not self.update:
            return
        current_version = self.data.get('version')
        if not version.is_greater_version(VERSION, current_version):
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
                    f'Version missmatch: {remote_ver=}, {local_ver=}')
            if remote_ts and local_ts and remote_ts > local_ts:
                return data
        return self._open(file_path, ssh_params, path_to_original, 'rb', check)

    def merge(self, password, data, file_path, ssh_params, path_to_original):
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
        def read(fh, path_to_original):
            if path_to_original:
                self.data = pickle.loads(
                    steganography.read(fh, path_to_original))
            else:
                self.data = pickle.load(fh)
        self._open(file_path, ssh_params, path_to_original, 'rb', read)
        self._locked = True

    def save(self, file_path, ssh_params=None, path_to_original=None):
        def write(fh, path_to_original):
            if path_to_original:
                steganography.write(
                    fh, path_to_original, pickle.dumps(self.data))
            else:
                fh.write(pickle.dumps(self.data))
        self.data['timestamp'] = datetime.datetime.utcnow()
        self.data['version'] = VERSION
        self._open(file_path, ssh_params, path_to_original, 'wb', write)

    def load_clear(self, fh):
        """Load data from open file containing clear text data."""
        if self.locked:
            raise VaultError('Vault is locked, unlock first!')
        self._locked = False
        for row in fh:
            self.add(ast.literal_eval(row.strip()))

    def save_clear(self, fh):
        """Save data in open file as clear text."""
        if self.locked:
            raise VaultError('Vault is locked, please unlock first')
        for obj in self.data['vault']:
            print(repr(obj), file=fh)

    def lock(self, password):
        """Lock vault with password."""
        if self._locked:
            return
        data = pickle.dumps(self.data['vault'])
        key = self.create_key(password,
                              self.data['salt'],
                              self.data.get('iterations', 1000000))
        self.data['vault'] = Fernet(key).encrypt(data)
        self._locked = True

    def unlock(self, password):
        """Unlock vault with password."""
        if not self._locked:
            return self.data
        data = self._unlock(password, self.data)
        if data:
            self.data = data
            self._locked = False
        return data

    def _unlock(self, password, data):
        key = self.create_key(password,
                              data['salt'],
                              data.get('iterations', 1000000))
        try:
            data['vault'] = pickle.loads(Fernet(key).decrypt(data['vault']))
            return data
        except InvalidToken:
            pass

    @staticmethod
    def create_key(password, salt, iterations=1000000):
        """Create a key to be used."""
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
        """Get objects in their current state in vault."""
        return self.data['vault']

    def set_objects(self, objs):
        """Set vault content to input."""
        if not self.locked:
            self.data['vault'] = []
            for obj in objs:
                self.add(obj)

    def add(self, obj):
        """Add to vault content."""
        self.data['vault'].append(obj)
        self.data['timestamp'] = datetime.datetime.utcnow()

    def replace(self, obj):
        for index, current_obj in enumerate(self.data['vault']):
            if current_obj['uid'] == obj['uid']:
                self.data['vault'][index] = obj
                self.data['timestamp'] = datetime.datetime.utcnow()
                return True

    def remove_password(self, obj):
        """Remove obj from vault if it exists."""
        self.data['vault'].remove(obj)

    def remove_deleted(self):
        now = datetime.datetime.now()
        keep = datetime.timedelta(days=KEEP_DAYS)
        before = len(self.data['valut'])
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
