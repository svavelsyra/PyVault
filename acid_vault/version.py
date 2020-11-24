import os.path

__all__ = [
    "__title__",
    "__summary__",
    "__uri__",
    "__version__",
    "__commit__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
]


try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    base_dir = None


__title__ = "acid_vault"
__summary__ = "Python Password Vault"
__uri__ = "https://github.com/svavelsyra/PyVault"

__version__ = "1.0.0"

if base_dir is not None and os.path.exists(os.path.join(base_dir, ".commit")):
    with open(os.path.join(base_dir, ".commit")) as fp:
        __commit__ = fp.read().strip()
else:
    __commit__ = None

__author__ = "Nils Nyman-Waara"
__email__ = "acid_vault@h2so4.se"

__license__ = "GNU Affero General Public License v3"
__copyright__ = "2020 %s" % __author__
