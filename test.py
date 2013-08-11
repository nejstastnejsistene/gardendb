import pickle
from gardendb import *

# Test version 0.
Test = cucumber('Test', 'foo bar foobar', version=0)

# Create and pickle a Test object.
old_test = Test(1, 2, 3)
old_test_pickle = pickle.dumps(old_test, 2)

# Test version 1.
Test = cucumber('Test', 'foo bar foobar new_field', version=1)

# Test version 2.
Test = cucumber('Test', 'foo bar foobar new_field', version=2)

# Migration from version 0 to 1.
@Test.migrate_from(0, 1)
def add_new_field(foo, bar, foobar):
    return (foo, bar, foobar, 'this is a new field')

# Migration from version 1 to 2.
@Test.migrate_from(1, 2)
def increment_foobar(foo, bar, foobar, new_field):
    return (foo, bar, foobar + 1, new_field)

# Unpickle the original object, and notice that it has automatically
# performed the necessary migrations.
migrated_test = pickle.loads(old_test_pickle)
print migrated_test

import collections

Point = collections.namedtuple('Point', 'x y')
print len(pickle.dumps(Point(1, 2), pickle.HIGHEST_PROTOCOL))
Point = cucumber('Point', 'x y')
print len(pickle.dumps(Point(1, 2), pickle.HIGHEST_PROTOCOL))

# Keyword args
p = Point(x=1, y=2)
print p
print eval(repr(p))

try:
    # Import cucumber.psycopg2 to enable automatic type conversion to
    # postgresql types.
    import psycopg2
    import gardendb.postgres

    Ahoj = cucumber('Ahoj', 'dobry den')
    ahoj = Ahoj('na', 'shledanou')

    conn = psycopg2.connect(database='template1')
    with conn.cursor() as cur:
        gardendb.postgres.init(cur)
        cur.execute('INSERT INTO cucumber VALUES (%s)', (ahoj,))
        cur.execute('SELECT foo FROM cucumber')
        print cur.fetchone()[0]
    conn.close()
except Exception, e:
    print 'unable to run psycopg2 test:', e
