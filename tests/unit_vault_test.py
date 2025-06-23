import pickle
import os
from tests.fixtures import *
import acid_vault.vault.vault as vault

def test_unlock(vault_data_locked):
    """Test unlocking a locked vault with the correct password."""
    v = vault.Vault()
    v.data = vault_data_locked
    v._locked = True
    v.unlock('testpass')
    assert 'test' in v.data['vault']

def test_already_unlocked(vault_data_unlocked):
    """Test that unlocking an already unlocked vault returns the data."""
    v = vault.Vault()
    v.data = vault_data_unlocked
    v.unlock('testpass')
    assert 'test' in v.data['vault']

def test_lock(vault_data_unlocked):
    """Test locking an unlocked vault."""
    v = vault.Vault()
    v.data = vault_data_unlocked
    v.lock('testpass')
    try:
        assert 'test' not in v.data['vault']
    except TypeError:
        # v.data is a binary string so should trhow error
        pass
    assert b'test' not in v.data['vault']

def test_load_file(locked_file):
    """Test loading an encrypted file.

    This test covers loading a vault from a file without using
    steganography or SSH.
    """
    v = vault.Vault()
    v.load(locked_file)
    v.unlock('testpass')
    assert 'test' in v.data['vault']

def test_save_file(vault_data_locked, tmpdir):
    """Test saving an encrypted file.

    This test covers saving a vault to a file without using
    steganography or SSH.
    """
    v = vault.Vault()
    v.data = vault_data_locked
    f = tmpdir.join('testfile.txt')
    v.save(f)
    v2 = vault.Vault()
    v2.load(f)
    v2.unlock('testpass')
    assert 'test' in v2.data['vault']

def test_load_clear(tmpdir, vault_data_unlocked):
    """Test loading passwords from a clear text file."""
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
