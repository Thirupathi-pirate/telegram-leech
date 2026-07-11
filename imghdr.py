"""Minimal imghdr shim for Python 3.13+ (removed from stdlib)."""
import struct

def what(file=None, h=None):
    if h is None:
        if file is None:
            return None
        if hasattr(file, 'read'):
            h = file.read(32)
        else:
            with open(file, 'rb') as f:
                h = f.read(32)
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if h[:3] == b'GIF':
        return 'gif'
    if h[:2] in (b'BM',):
        return 'bmp'
    if h[:2] == b'\xff\xd8':
        return 'jpeg'
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'
    if h[:4] in (b'\x00\x00\x01\x00', b'\x00\x00\x02\x00'):
        return 'tiff'
    return None
