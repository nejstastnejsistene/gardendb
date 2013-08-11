import binascii
import psycopg2
from psycopg2.errorcodes import DUPLICATE_TABLE
from psycopg2.extensions import AsIs, ISQLQuote, new_type, \
                                register_type, register_adapter

try:
    import cPickles as pickle
except ImportError:
    import pickle

from . import cucumber_add_ons


def adapt_bytea(obj):
    '''Adapt an object using getquoted().'''
    p = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    return psycopg2.Binary(p)


def cast_bytea(value, cur):
    '''Convert a bytea to a python value by unpickling.'''
    try:
        return pickle.loads(binascii.unhexlify(value[2:]))
    except pickle.UnpicklingError:
        mesg = 'unable to unpickle bytea: {!r}'.format(value)
        raise psycopg2.InterfaceError(mesg)


def add_adapter(cls):
    '''Register adapt_bytea() with this class.'''
    register_adapter(cls, adapt_bytea) 
    return cls


# Register cast_bytea with psycopg2.
PICKLE = new_type(psycopg2.BINARY.values, 'PICKLE', cast_bytea)
register_type(PICKLE)

# Register newly created cucumbers with psycopg2.
cucumber_add_ons.append(add_adapter)


def dummy_pool(conn):
    class DummyPool(object):
        def getconn(self):
            return conn
        def putconn(self, conn):
            pass
    return DummyPool()


class Cucumber(object):

    def_fmt = '''
    CREATE TABLE {name}
        ( key   varchar   NOT NULL UNIQUE
        , value bytea     NOT NULL
        , mtime timestamp NOT NULL DEFAULT localtimestamp
        )
    '''

    replace_fmt = '''
    CREATE RULE "replace_{name}" AS
        ON INSERT TO "{name}"
        WHERE
            EXISTS(SELECT 1 FROM {name} WHERE key=NEW.key)
        DO INSTEAD
            UPDATE {name}
            SET value = NEW.value, mtime = localtimestamp
            WHERE key = NEW.key
    '''

    select_fmt = 'SELECT value FROM {name} WHERE key = %s'
    insert_fmt = 'INSERT INTO {name} (key, value) VALUES (%s, %s)'

    def __init__(self, cls, pool):
        self.cls = cls
        self.pool = pool

        # Convert CamelCase to camel_case.
        cls_name = cls.__name__
        name = [cls_name[0].lower()]
        for c in cls_name[1:]:
            if c.isupper():
                name += ['_', c.lower()]
            else:
                name.append(c)
        self.name = ''.join(name)

        # Format the class name into the table and rule definitions.
        self.table_def = self.def_fmt.format(name=self.name)
        self.replace_cmd = self.replace_fmt.format(name=self.name)
        self.select_cmd = self.select_fmt.format(name=self.name)
        self.insert_cmd = self.insert_fmt.format(name=self.name)

        conn = self.pool.getconn()

        # Create the table and replacement rule if not already defined.
        with conn.cursor() as cur:

            cur.execute('''
                SELECT 1 FROM pg_tables WHERE tablename = '{name}'
                '''.format(name=self.name))
            if not cur.fetchone():
                cur.execute(self.table_def)

            cur.execute('''
                SELECT 1 FROM pg_rules WHERE rulename = 'replace_{name}'
                '''.format(name=self.name))
            if not cur.fetchone():
                cur.execute(self.replace_cmd)

        conn.commit()
        self.pool.putconn(conn)

    def __getitem__(self, key):
        ''''''
        if not isinstance(key, basestring):
            raise ValueError, 'keys must be strings'

        conn = self.pool.getconn()
        with conn.cursor() as cur:
            cur.execute(self.select_cmd, (key,))
            value = cur.fetchone()
        self.pool.putconn(conn)

        if value is not None:
            value = value[0]
        return value

    def __setitem__(self, key, value):
        if not isinstance(key, basestring):
            raise ValueError, 'keys must be strings'

        conn = self.pool.getconn()
        with conn.cursor() as cur:
            cur.execute(self.insert_cmd, (key, value))
        conn.commit()
        self.pool.putconn(conn)
