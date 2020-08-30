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

VALID_PASSWORD_TYPES = ('alpha', 'alphanum', 'alphanumspecial', 'mobilealpha', 'mobilealphanum', 'mobilealphanumspecial')


class Vault():
    def __init__(self, password, data_file=None):
        self.password = password
        if data_file:
            self.read(data_file)
        else:
            self.data = {'salt': os.urandom(16),
                         'vault': []}
            self.key = None

    def read(self, fh):
        self.data = pickle.load(fh)
        self.create_key()
        try:
            data = Fernet(self.key).decrypt(self.data['vault'])
        except InvalidToken:
            self.data['vault'] = []
            print('InvalidToken')
            return
        self.data['vault'] = pickle.loads(data)

    def write(self, fh):
        data = pickle.dumps(self.data['vault'])
        key = self.key or self.create_key()
        self.data['vault'] = Fernet(self.key).encrypt(data)
        pickle.dump(self.data, fh)

    def create_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.data['salt'],
            iterations=1000000,
            backend=default_backend()
            )
        self.key = base64.urlsafe_b64encode(
            kdf.derive(bytearray(self.password, 'utf-8')))

    def get_objects(self):
        return self.data['vault']

    def set_objects(self, objs):
        self.data['vault'] = objs
    
    def add(self, obj):
        self.data['vault'].append(obj)

    def remove_password(self, obj):
        self.data['vault'].remove(obj)

def generate_password(password_type='alpha', n=10):
    alphabets = {'alpha': (string.ascii_letters, 'isupper', 'islower'),
                 'alphanum': (string.ascii_letters + string.digits, 'isupper', 'islower','isdigit'),
                 'alphanumspecial': (string.ascii_letters + string.digits + '!"#¤%&/()=?', 'isupper', 'islower','isdigit'),
                 'mobilealpha': (string.ascii_lowercase, 'islower'),
                 'mobilealphanum': (string.ascii_lowercase, 'islower'),
                 'mobilealphanumspecial': (string.ascii_lowercase, 'islower'),}
    if not password_type in alphabets:
        raise KeyError(f'Password type has to be one of the following: {", ".join(alphabets.keys())} it is "{password_type}".')
    while True:
        alphabet = alphabets[password_type][0]
        password = random.choices(alphabet, k=n)
        if password_type.startswith('mobile'):
            password[0] = password[0].upper()
        if 'mobilealphanum' in password_type :
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
