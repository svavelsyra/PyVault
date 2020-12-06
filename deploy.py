import os
import subprocess
import sys

from acid_vault.version import __version__

for filename in os.listdir('dist'):
    os.remove(os.path.join('dist', filename))

p = subprocess.Popen([sys.executable, 'setup.py', 'sdist', 'bdist_wheel'])
p.wait()
p = subprocess.Popen(['twine', 'upload', '-r', 'pypi', 'dist/*'])
p.wait()

p = subprocess.Popen(['pyinstaller',
                      'install.py',
                      '-F',
                      '-n',
                      f'PyVault-Win-Install-v{__version__}',
                      '--add-data',
                      'install data;install data'])
p.wait()
