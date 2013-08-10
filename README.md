gardendb (WIP)
============== 
Simple python flat-file databases with Cucumbers: simple, version-controlled records with streamlined pickle representations.

## Streamlined Pickle Representations

```python
import collections
import pickle
from cucumber import *

# Point created with namedtuple.
Point = collections.namedtuple('Point', 'x y')
print len(pickle.dumps(Point(1, 2), pickle.HIGHEST_PROTOCOL))
# 35

# Point created with cucumber.
Point = cucumber('Point', 'x y')
print len(pickle.dumps(Point(1, 2), pickle.HIGHEST_PROTOCOL))
# 94
```

## Example Cucumber Usage

```python
import pickle
from cucumber import *

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
```

## Seamless psycopg2 conversion

```python
import psycopg2

# Import cucumber.psycopg2 to enable automatic type conversion to
# the postgresql bytea type.
import cucumber.postgres

# Database template1 has a table called cucumber which has a
# single row called foo with type bytea.
conn = psycopg2.connect(database='template1')

with conn.cursor() as cur:
    # Initialization must happen once before anything else.
    cucumber.postgres.init(cur)

    # Inserting a python value into a bytea automatically pickles it first.
    cur.execute('INSERT INTO cucumber VALUES (%s)', (migrated_test,))

    # Retrieving the bytea unpickles it.
    cur.execute('SELECT foo FROM cucumber')

    # Same as before:
    print cur.fetchone()[0]
    # Test(foo=1, bar=2, foobar=4, new_field='this is a new field')

conn.close()
```
