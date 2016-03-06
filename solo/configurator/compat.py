""" Parts of this module are taken from ``pyramid.compat`` module
"""
string_types = str,
integer_types = int,
class_types = type,
text_type = str
binary_type = bytes
long = int
def is_nonstr_iter(v):
    if isinstance(v, str):
        return False
    return hasattr(v, '__iter__')



def text_(s, encoding='latin-1', errors='strict'):
    """  This function is a copy of ``pyramid.compat.text_``

    If ``s`` is an instance of ``binary_type``, return
    ``s.decode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, bytes):
        return s.decode(encoding, errors)
    return s # pragma: no cover

def bytes_(s, encoding='latin-1', errors='strict'):
    """ This function is a copy of ``pyramid.compat.bytes_``

    If ``s`` is an instance of ``text_type``, return
    ``s.encode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, str): # pragma: no cover
        return s.encode(encoding, errors)
    return s
