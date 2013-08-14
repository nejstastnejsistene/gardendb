import binascii
import psycopg2
from psycopg2.extensions import new_type, register_type

try:
    import cPickles as pickle
except ImportError:
    import pickle

from . import BaseGarden


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


class PgGarden(BaseGarden):

    table_def_fmt = '''
    CREATE TABLE {name}
        ( key   bytea     NOT NULL UNIQUE
        , value bytea     NOT NULL
        , mtime timestamp NOT NULL DEFAULT localtimestamp
        )
    '''

    replace_def_fmt = '''
    CREATE RULE "replace_{name}" AS
        ON INSERT TO "{name}"
        WHERE
            EXISTS(SELECT 1 FROM {name} WHERE key=NEW.key)
        DO INSTEAD
            UPDATE {name}
            SET value = NEW.value, mtime = localtimestamp
            WHERE key = NEW.key
    '''

    select_all_cmd_fmt = 'SELECT key, value FROM {name}'
    select_cmd_fmt = 'SELECT value FROM {name} WHERE key = %s'
    insert_cmd_fmt = 'INSERT INTO {name} (key, value) VALUES '
    delete_cmd_fmt = 'DELETE FROM {name} WHERE key = %s'

    def __init__(self, name, pool, cls=None):
        BaseGarden.__init__(self, cls)
        self.name = name
        self.pool = pool

        # Format the various sql commands that we use.
        for name, value in PgGarden.__dict__.items():
            if name.endswith('_fmt'):
                setattr(self, name[:-4], value.format(name=self.name))

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
        return {k: self.unpack_state(v) for k, v in pairs}

    def putmany(self, dct):
        '''Place/replace many cucumbers into the Garden.'''
        if not dct:
            # Silently ignore requests to put nothing.
            return
        # Pack values.
        dct = {k: self.pack_state(v) for k, v in dct.items()}
        # Calculate the SQL command format.
        cmd = self.insert_cmd + ', '.join(['(%s, %s)'] * len(dct))
        # Generate the SQL parameters.
        args = []
        for pair in dct.items():
            args += map(adapt_bytea, pair)

        conn = self.pool.getconn()
        with conn.cursor() as cur:
            cur.execute(cmd, args)
        conn.commit()
        self.pool.putconn(conn)

    def __getitem__(self, key):
        '''Retrieve a cucumber from the Garden.'''

        _key = adapt_bytea(key)

        conn = self.pool.getconn()
        with conn.cursor() as cur:
            cur.execute(self.select_cmd, (_key,))
            value = cur.fetchone()
        self.pool.putconn(conn)

        if value is None:
            raise KeyError, key
        return self.unpack_state(value[0])

    def __setitem__(self, key, value):
        '''Place/replace a cucumber into the Garden.'''
        self.putmany({key: value})

    def __delitem__(self, key):
        '''Delete a cucumber from the Garden.
        
           If the key does not exist, no exception is raised.'
        '''

        key = adapt_bytea(key)

        conn = self.pool.getconn()
        with conn.cursor() as cur:
            cur.execute(self.delete_cmd, (key,))
        conn.commit()
        self.pool.putconn(conn)
