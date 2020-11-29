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

from PIL import Image
import pickle

def write(fh, original, data):
    with Image.open(original) as image:
        mask = [int(y) for y in ''.join([str(format(x, 'b')).zfill(8) for x in data])]
        new_band = []
        for index, x in enumerate(image.getdata(0)):
            new_band.append((x + (mask.pop(0) if mask else 2)%255))

        r,g,b = image.split()
        r.putdata(new_band)
        i = Image.merge(image.mode, (r, g, b))
        i.save(fh, 'png')

def read(fh, original):
    with Image.open(original) as orig, Image.open(fh) as mask:
        orig = list(orig.getdata(0))
        mask = list(mask.getdata(0))
        result = []
        for x, y in zip(mask, orig):
            value = x - y 
            if value in (2, -254):
                break
            if value < 0:
                value = 1
            result.append(str(value))
        return int(''.join(result), 2).to_bytes(len(result) // 8, byteorder='big')
