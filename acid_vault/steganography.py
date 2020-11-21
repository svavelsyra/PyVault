import io
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
