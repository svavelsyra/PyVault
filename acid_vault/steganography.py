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

'''
Steganography
Hides data within an image so that its not obvious that the data is
there.
'''

from PIL import Image


class SteganographyError(Exception):
    '''StganographyError for various error situations.'''
    pass

def write(fh, original, data):
    '''
    Combine data with data from original (image (tested on jpg))
    and write it as a .png image in opened file.
    '''
    with Image.open(original) as image:
        mask = [int(y) for y in ''.join([str(format(x, 'b')).zfill(8) for
                                         x in data])]
        bands = image.split()
        for band_index in (0, 1, 2):
            new_band = []
            for index, x in enumerate(image.getdata(band_index)):
                new_band.append((x + (mask.pop(0) if mask else 2) % 255))
            bands[band_index].putdata(new_band)
            if not mask:
                break
        else:
            raise SteganographyError('Ran out of image space')
        i = Image.merge(image.mode, bands)
        i.save(fh, 'png')


def read(fh, original):
    '''
    Read data from opened file and compare it to orignal to get stored data.
    '''
    def convert_result(result):
        return int(''.join(result), 2).to_bytes(len(result) // 8,
                                                byteorder='big')
    with Image.open(original) as orig, Image.open(fh) as mask:
        result = []
        for band_index in (0, 1, 2):
            orig_data = list(orig.getdata(band_index))
            mask_data = list(mask.getdata(band_index))
            for x, y in zip(mask_data, orig_data):
                value = x - y
                if value in (2, -254):
                    return convert_result(result)
                if value < 0:
                    value = 1
                result.append(str(value))
        return convert_result(result)
