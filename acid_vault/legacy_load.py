def legacy_load(obj):
    version = obj.get('version')
    if not version:
        obj['version'] = '1.0.0'
        values = obj.get('attributes', {}).get('ssh_config')
        if values:
            obj['attributes']['ssh_config'] = {}
            for index, key  in enumerate(('host', 'port', 'username', 'password')):
                try:
                    obj['attributes']['ssh_config'][key] = values[index]
                except IndexError as err:
                    obj['attributes']['ssh_config'][key] = ''
    return obj
