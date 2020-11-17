from tests.fixtures import *
import vault.vault as vault

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
    
def test_lock():
    pass
