import argparse
import os
import subprocess
import sys

from acid_vault.version import __version__


def tox():
    p = subprocess.Popen(['tox'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    print(p.stdout.readlines())
    print(p.stderr.readlines())
    print('Tests completed')
    return p.returncode


def clean():
    for filename in os.listdir('dist'):
        os.remove(os.path.join('dist', filename))
    print('Cleaned')
    return 0


def build():
    p = subprocess.Popen([sys.executable, 'setup.py', 'sdist', 'bdist_wheel'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    p.wait()
    print(p.stdout.readlines())
    print(p.stderr.readlines())
    print('Building')
    return p.returncode


def upload():
    p = subprocess.Popen(['twine', 'upload', '-r', 'pypi', 'dist/*'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    p.wait()
    print(p.stdout.readlines())
    print(p.stderr.readlines())
    print('Upload completed')
    return p.returncode


def build_win():
    p = subprocess.Popen(['pyinstaller',
                          'install.py',
                          '-F',
                          '-n',
                          f'PyVault-Win-Install-v{__version__}',
                          '--add-data',
                          'install data;install data',
                          '--distpath',
                          'win_installers'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    p.wait()
    print(p.stdout.readlines())
    print(p.stderr.readlines())
    print('Windows installer built completed')
    return p.returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy PyVault.')
    parser.add_argument(
        '-c', action='store_true', help='Clean dist directory first.')
    parser.add_argument(
        '-b', action='store_true', help='Build.')
    parser.add_argument(
        '-u', action='store_true', help='Upload dists to pypi.')
    parser.add_argument(
        '-w', action='store_true', help='Build windows Installer.')
    parser.add_argument(
        '-t', action='store_true', help='Run Tox on project.')
    parser.add_argument(
        '-f', action='store_true', help='Force deploy even if checks fails')
    args = parser.parse_args()
    if not [x for x in 'bctuw' if getattr(args, x)]:
        # No run flags set, set default to run all.
        # -f is excluded in check.
        # [setattr(args, x, True) for x in 't']
        [setattr(args, x, True) for x in 'cbuw']
    result = 0
    for flag, step in (('t', tox),
                       ('c', clean),
                       ('b', build),
                       ('u', upload),
                       ('w', build_win)):
        if getattr(args, flag):
            result = step() or result
            if result and not args.f:
                exit(result)
    print(result)
    exit(result)
