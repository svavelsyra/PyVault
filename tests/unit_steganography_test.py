import hashlib
import PIL
import pytest

from tests.fixtures import *
import acid_vault.steganography as steganography
from acid_vault.steganography import SteganographyError

def test_write(tmpdir):
    expected = 'ce91ce323ab4c03f705bc37c5071af1c'
    data = b'Test string to write'
    file_path = tmpdir.join('outfile.png')
    original_path = os.path.join(os.path.dirname(__file__),
                                 "test_data",
                                 "test.jpg")
    with open(file_path, 'bw') as fh:
        steganography.write(fh, original_path, data)
    with open(file_path, 'br') as fh:
        assert hashlib.md5(fh.read()).hexdigest() == expected


def test_read():
    expected = b'Test string to write'
    original_path = os.path.join(os.path.dirname(__file__),
                                 "test_data",
                                 "test.jpg")
    written_path = os.path.join(os.path.dirname(__file__),
                                "test_data",
                                "test.png")
    with open(written_path, 'rb') as fh:
        assert steganography.read(fh, original_path) == expected

def test_to_large(tmpdir):
    file_path = tmpdir.join('outfile.png')
    original_path = os.path.join(os.path.dirname(__file__),
                                 "test_data",
                                 "test.jpg")
    with PIL.Image.open(original_path) as image:
        data = b'a'*len(image.getdata())
    with open(file_path, 'bw') as fh:
        with pytest.raises(SteganographyError):
            steganography.write(fh, original_path, data)