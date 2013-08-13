import binascii
import psycopg2
from psycopg2.extensions import new_type, register_type

try:
    import cPickles as pickle
except ImportError:
    import pickle


def adapt_bytea(obj):
    '''Adapt an object to a bytea by pickling.'''
    p = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    return psycopg2.Binary(p)


def cast_bytea(value, cur):
    '''Convert a bytea to a python value by unpickling.'''

    # Decode the bytea using the original typecast object.
    value = psycopg2.BINARY(value, cur)
    try:
        return pickle.loads(value)
    except pickle.UnpicklingError:
        mesg = 'unable to unpickle buffer: {!r}'.format(value)
        raise psycopg2.InterfaceError(mesg)


# Register cast_bytea with psycopg2.
PICKLE = new_type(psycopg2.BINARY.values, 'PICKLE', cast_bytea)
register_type(PICKLE)


def dummy_pool(conn):
    class DummyPool(object):
        def getconn(self):
            return conn
        def putconn(self, conn):
            pass
    return DummyPool()


class Garden(object):
    '''A place to store your cucumbers.'''

    def_fmt = '''
    CREATE TABLE {name}
        ( key   bytea     NOT NULL UNIQUE
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

    select_all_fmt = 'SELECT key, value FROM {name}'
    select_fmt = 'SELECT value FROM {name} WHERE key = %s'
    insert_fmt = 'INSERT INTO {name} (key, value) VALUES (%s, %s)'

    def __init__(self, name, pool):
        self.name = name
        self.pool = pool

        # Format the class name into the table and rule definitions.
        self.table_def = self.def_fmt.format(name=self.name)
        self.replace_def = self.replace_fmt.format(name=self.name)
        self.select_all_cmd = self.select_all_fmt.format(name=self.name)
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
                cur.execute(self.replace_def)

        conn.commit()
        self.pool.putconn(conn)

    def getall(self):
        conn = self.pool.getconn()
        with conn.cursor() as cur:
            cur.execute(self.select_all_cmd)
            pairs = cur.fetchall()
        self.pool.putconn(conn)
        return dict(pairs)

    def __getitem__(self, key):
        '''Retrieve a cucumber from the Garden.'''

        key = adapt_bytea(key)

        conn = self.pool.getconn()
        with conn.cursor() as cur:
            cur.execute(self.select_cmd, (key,))
            value = cur.fetchone()
        self.pool.putconn(conn)

        if value is not None:
            value = value[0]
        return value

    def __setitem__(self, key, value):
        '''Place/replace a cucumber into the Garden.'''

        key = adapt_bytea(key)
        value = adapt_bytea(value)

        conn = self.pool.getconn()
        with conn.cursor() as cur:
            cur.execute(self.insert_cmd, (key, value))
        conn.commit()
        self.pool.putconn(conn)
