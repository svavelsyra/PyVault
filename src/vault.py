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
        self.key = base64.urlsafe_b64encode(kdf.derive(bytearray(self.password, 'utf-8')))

    def add(self, obj):
        self.data['vault'].append(obj)

    def remove_password(self, obj):
        self.data['vault'].remove(obj)
