# -*- coding: utf-8 -*-

import io

from werkzeug.datastructures import FileStorage

from app.utils import validate_file_header


def _file(filename: str, data: bytes) -> FileStorage:
    return FileStorage(stream=io.BytesIO(data), filename=filename)


def test_validate_file_header_extended_binary_signatures():
    assert validate_file_header(_file('sample.tiff', b'II*\x00' + b'x' * 16)) is True
    assert validate_file_header(_file('sample.rar', b'Rar!\x1a\x07\x00' + b'x' * 16)) is True
    assert validate_file_header(_file('sample.7z', b"7z\xbc\xaf'\x1c" + b'x' * 16)) is True


def test_validate_file_header_heic_signature():
    heic = b'\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1'
    assert validate_file_header(_file('sample.heic', heic)) is True
    assert validate_file_header(_file('sample.heic', b'not-heic-data')) is False


def test_validate_file_header_textual_formats():
    svg = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
    assert validate_file_header(_file('sample.svg', svg)) is True
    assert validate_file_header(_file('sample.svg', b'\x00\x01not-svg')) is False

    assert validate_file_header(_file('sample.txt', b'hello world\n')) is True
    assert validate_file_header(_file('sample.txt', b'abc\x00def')) is False
