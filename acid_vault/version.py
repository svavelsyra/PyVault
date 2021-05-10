###############################################################################
# Acid Vault                                                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################
'''Version and other package constants.'''
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

'''
V.2.0.2 - UI no longer lock on OK in edit password
'''
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    base_dir = None


__title__ = "acid_vault"
__summary__ = "Python Password Vault"
__uri__ = "https://github.com/svavelsyra/PyVault"

__version__ = "2.0.2"

if base_dir is not None and os.path.exists(os.path.join(base_dir, ".commit")):
    with open(os.path.join(base_dir, ".commit")) as fp:
        __commit__ = fp.read().strip()
else:
    __commit__ = None

__author__ = "Nils Nyman-Waara"
__email__ = "acid_vault@h2so4.se"

__license__ = "GNU Affero General Public License v3"
__copyright__ = "2020 %s" % __author__


def same_minor_version(version1, version2=None):
    version2 = version2 or __version__
    try:
        version1 = version1.split('.')
        version2 = version2.split('.')
        return version1[0] == version2[0] and version1[1] == version2[1]
    except Exception as err:
        print(err)


def is_greater_version(version1, version2):
    if not (version2):
        return True
    v1 = [int(x) for x in version1.split('.')]
    v2 = [int(x) for x in version2.split('.')]
    return (
        v1[0] > v2[0] or
        (v1[0] == v2[0] and v1[1] > v2[1]) or
        (v1[0] == v2[0] and v1[1] == v2[1] and v1[2] > v2[2]))
