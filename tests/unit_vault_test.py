from tests.fixtures import *
import vault.vault

def test_unlock(vault_data):
    v = vault.vault.Vault()
    v.data = vault_data
    v.unlock('testpass')
    print(v.data['vault'])
    assert 'test' in v.data['vault']
