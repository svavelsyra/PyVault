import os
import platform

def data_dir():
    system = platform.system()
    if system == 'Windows':
        path = os.path.join('appdata', 'local', 'vault')
    elif system == 'Linux':
        path = '.vault'
    else:
        path = ''
    path = os.path.expanduser(os.path.join('~', path))
    os.makedirs(path, exist_ok=True)
    return path
