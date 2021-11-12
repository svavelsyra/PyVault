'''Handling of old formats.'''


def legacy_load(obj):
    '''Handle legacy state formats and update to new format.'''
    version = obj.get('version')
    if not version:
        obj['version'] = '1.0.0'
        values = obj.get('attributes', {}).get('ssh_config')
        if values:
            obj['attributes']['ssh_config'] = {}
            for index, key in enumerate(
                    ('host', 'port', 'username', 'password')):
                try:
                    obj['attributes']['ssh_config'][key] = values[index]
                except IndexError:
                    obj['attributes']['ssh_config'][key] = ''
    if obj['version'] == '1.0.0':
        obj['last_update'] = obj.get('attributes', {}).pop('last_update', False)
        obj['profiles'] = {'profile1':{'attributes': obj.pop('attributes', {}),
                                       'widgets': obj.pop('widgets', {})
                                       }}
        obj['last_profile'] = 'profile1'
        
    return obj
