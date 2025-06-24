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
"""
Constants.
"""

import os
import platform


def data_dir():
    """Returns path to programs data dir."""
    # Check for development environment by looking for a sentinel file.
    dev_sentinel = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.dev_sentinel')
    is_dev = os.path.exists(dev_sentinel)

    system = platform.system()
    if is_dev:
        path = os.path.join(os.path.dirname(dev_sentinel), 'dev_data')
    elif system == 'Windows':
        path = os.path.join('appdata', 'local', 'vault')
    elif system == 'Linux':
        path = '.vault'
    else:
        path = ''
    path = os.path.expanduser(os.path.join('~', path))
    os.makedirs(path, exist_ok=True)
    return path
