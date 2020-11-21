import pickle
import pytest

@pytest.fixture
def vault_data_locked():
    return {'salt': b'\xa0\x9b\xb4\xbe\xd1\xb7\xe0t\x11\x9a\xd2\xe2\x10\x04\x03\x7f',
            'iterations': 1000000,
            'vault': b'gAAAAABfsq0JevttlDtLkaD2QfQn96QDOFOyh1egDiatqTlDnE98zHJx9SbKLRAPuZLPl4X3JOZZq2FOA5sfawk6TSRTnIdQv-Ik3MCr_ZFGxVZ85EW6P9c='}

@pytest.fixture
def vault_data_unlocked():
    return {'salt': b'\xa0\x9b\xb4\xbe\xd1\xb7\xe0t\x11\x9a\xd2\xe2\x10\x04\x03\x7f',
            'iterations': 1000000,
            'vault': ['test']}

@pytest.fixture
def locked_file(tmpdir, vault_data_locked):
    file = tmpdir.join('testfile.txt')
    with open(file, 'bw') as fh:
        pickle.dump(vault_data_locked, fh)
    return file
