'''See http://pythonhosted.org/psycopg2/advanced.html'''
import binascii
import psycopg2
from psycopg2.extensions import AsIs, ISQLQuote, new_type, \
                                register_type, register_adapter

try:
    import cPickles as pickle
except ImportError:
    import pickle

from . import cucumber_add_ons

postgres_type = None

def init(cur):
    '''Register bytea with pscyopg2 for automatic unpickling.'''
    global postgres_type
    if postgres_type is None:
        cur.execute('SELECT NULL::bytea')
        bytea_oid = cur.description[0][1]
        postgres_type = new_type((bytea_oid,), 'BYTEA', cast_bytea)
        register_type(postgres_type)


def cast_bytea(value, cur):
    '''Convert a bytea to a python value by unpickling.'''
    try:
        return pickle.loads(binascii.unhexlify(value[2:]))
    except:
        raise InterfaceError('bad bytea representation: {!r}'.format(value))


def add_adapter(cls):
    '''Register adapt_bytea() with this class.'''
    register_adapter(cls, adapt_bytea) 
    return cls


def adapt_bytea(obj):
    '''Adapt an object using getquoted().'''
    return AsIs(getquoted(obj))


def getquoted(obj):
    '''Cast a python value to an SQL bytea through pickling.'''
    p = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    bytea = "E'\\\\x{0}'::bytea".format(binascii.hexlify(p))
    return bytea


# Add __conform__ and getquoted to the methods added to cucumbers.
cucumber_add_ons.append(add_adapter)
