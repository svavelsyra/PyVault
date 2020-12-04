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
import ast
import base64
import os
import pickle
import random
import string

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

VALID_PASSWORD_TYPES = ('alpha',
                        'alphanum',
                        'alphanumspecial',
                        'mobilealpha',
                        'mobilealphanum',
                        'mobilealphanumspecial',
                        'numerical')


class Vault():
    def __init__(self, data_file=None):
        self._locked = False
        if data_file:
            self.load_file(data_file)
        else:
            self.data = {'salt': os.urandom(16),
                         'iterations': 1000000,
                         'vault': []}

    @property
    def locked(self):
        return self._locked

    def load_data(self, data):
        self.data = pickle.loads(data)
        self._locked = True

    def save_data(self):
        return pickle.dumps(self.data)

    def load_file(self, fh):
        self.data = pickle.load(fh)
        self._locked = True

    def save_file(self, fh):
        pickle.dump(self.data, fh)

    def load_clear(self, fh):
        if self.locked:
            raise VaultError('Vault is locked, unlock first!')
        self._locked = False
        for row in fh:
            self.add(ast.literal_eval(row.strip()))

    def save_clear(self, fh):
        if self.locked:
            raise VaultError('Vault is locked, please unlock first')
        for obj in self.data['vault']:
            print(repr(obj), file=fh)

    def lock(self, password):
        if self._locked:
            return
        data = pickle.dumps(self.data['vault'])
        key = self.create_key(password,
                              self.data['salt'],
                              self.data.get('iterations', 1000000))
        self.data['vault'] = Fernet(key).encrypt(data)
        self._locked = True

    def unlock(self, password):
        if not self._locked:
            return
        key = self.create_key(password,
                              self.data['salt'],
                              self.data.get('iterations', 1000000))
        try:
            self.data['vault'] = pickle.loads(Fernet(key).decrypt(
                self.data['vault']))
            self._locked = False
        except InvalidToken:
            pass

    def create_key(self, password, salt, iterations=1000000):
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
        return self.data['vault']

    def set_objects(self, objs):
        self.data['vault'] = objs

    def add(self, obj):
        self.data['vault'].append(obj)

    def remove_password(self, obj):
        self.data['vault'].remove(obj)


class VaultError(Exception):
    pass


def generate_password(password_type='alpha', n=10):
    alphabets = {'alpha': (string.ascii_letters, 'isupper', 'islower'),
                 'alphanum': (string.ascii_letters + string.digits, 'isupper', 'islower', 'isdigit'),  # noqa: E501 Line to long
                 'alphanumspecial': (string.ascii_letters + string.digits + '!"#¤%&/()=?', 'isupper', 'islower', 'isdigit'),  # noqa: E501 Line to long
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
