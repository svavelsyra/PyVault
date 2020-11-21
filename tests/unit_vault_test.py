import pickle

from tests.fixtures import *
import acid_vault.vault as vault

def test_unlock(vault_data_locked):
    v = vault.Vault()
    v.data = vault_data_locked
    v._locked = True
    v.unlock('testpass')
    assert 'test' in v.data['vault']

def test_already_unlocked(vault_data_unlocked):
    v = vault.Vault()
    v.data = vault_data_unlocked
    v.unlock('testpass')
    assert 'test' in v.data['vault']
    
def test_lock(vault_data_unlocked):
    v = vault.Vault()
    v.data = vault_data_unlocked
    v.lock('testpass')
    try:
        assert 'test' not in v.data['vault']
    except TypeError:
        # v.data is a binary string so should trhow error
        pass
    assert b'test' not in v.data['vault']
    
def test_load_data(vault_data_locked):
    data = pickle.dumps(vault_data_locked)
    v = vault.Vault()
    v.load_data(data)
    v.unlock('testpass')
    assert 'test' in v.data['vault']

def test_save_data(vault_data_locked):
    v = vault.Vault()
    v.data = vault_data_locked
    data = v.save_data()
    v2 = vault.Vault()
    v2.load_data(data)
    v2.unlock('testpass')
    assert 'test' in v2.data['vault']

def test_load_file(locked_file):
    v = vault.Vault()
    with open(locked_file, 'rb') as fh:
        v.load_file(fh)
    v.unlock('testpass')
    assert 'test' in v.data['vault']

def test_save_file(vault_data_locked, tmpdir):
    v = vault.Vault()
    v.data = vault_data_locked
    f = tmpdir.join('testfile.txt')
    with open(f, 'wb') as fh:
        v.save_file(fh)
    v2 = vault.Vault()
    with open(f, 'rb') as fh:
        v2.load_file(fh)
    v2.unlock('testpass')
    assert 'test' in v2.data['vault']

def test_load_clear(tmpdir, vault_data_unlocked):
    v = vault.Vault()
    v._locked = False
    v.data = vault_data_unlocked
    v.data['vault'] = []
    f = tmpdir.join('testfile.txt')
    with open(f, 'w') as fh:
        print('("test", )', file=fh)
    with open(f, 'r') as fh:
        v.load_clear(fh)
    assert ("test", ) in v.data['vault']
    
