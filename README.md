gardendb
========
Simple python flat-file databases with Cucumbers: simple, version-controlled records with streamlined pickle representations.

## Installation

To install from PyPI:

    pip install gardendb

Or, if you prefer to build from source:

    git clone git@github.com:nejstastnejsistene/gardendb.git
    cd gardendb
    python setup.py install

## Streamlined Pickle Representations

```python
import collections
import pickle
from cucumber import *

# Point created with cucumber.
Point = cucumber('Point', 'x y')
print len(pickle.dumps(Point(1, 2), pickle.HIGHEST_PROTOCOL))
# 35

# Point created with namedtuple.
Point = collections.namedtuple('Point', 'x y')
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

## Seamless psycopg2 Conversion

```python
import psycopg2
import random

import gardendb
import gardendb.postgres

# Read db settings and open a connection.
with open('.dbconfig') as f:
    conn = psycopg2.connect(f.read())
    
ThisIsACucumber= gardendb.cucumber('ThisIsACucumber', 'a b c')

# Create a Garden to put our cucumbers in. It expects a pool so
# lets create a dummy one using our connection.
pool = gardendb.postgres.dummy_pool(conn)
garden = gardendb.postgres.Garden(ThisIsACucumber, pool)

# Create a random test cucumber.
test = ThisIsACucumber(*(random.getrandbits(32) for i in range(3)))

# Insert and then retrieve the database.
with conn.cursor() as cur:

    # Inserting our random cucumber.
    garden['ahoj'] = test
    print garden['ahoj']
    # ThisIsACucumber(a=1626149735L, b=1648972953L, c=878265730L)

    # Any pickleable value can be stored. 
    my_garden['not_a_cucumber'] = range(10)
    print my_garden['not_a_cucumber']
    # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    # Any object can be used as a key as well.
    my_garden[1, 2, 3] = "key isn't a string".split()
    print my_garden[1, 2, 3]
    # ['key', "isn't", 'a', 'string']

    import pprint

    # The `getall` method returns a dictionary of all values.
    pprint.pprint(my_garden.getall())
    # {'ahoj': ThisIsACucumber(a=2483388665L, b=1153744226L, c=1011563634L),
    #  'not_a_cucumber': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    #  (1, 2, 3): ['key', "isn't", 'a', 'string']}

    # The `del` statement works as expected.
    del my_garden['ahoj']
    pprint.pprint(my_garden.getall())
    # {'not_a_cucumber': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    #  (1, 2, 3): ['key', "isn't", 'a', 'string']}

    # The putmany() function will insert many cucumbers in one go.
    dct = { x: x**2 for x in range(20) }
    my_garden.putmany(dct)
    pprint.pprint(my_garden.getall())
    # {0: 0,
    #  1: 1,
    #  2: 4,
    #  3: 9,
    #  4: 16,
    #  5: 25,
    #  6: 36,
    #  7: 49,
    #  8: 64,
    #  9: 81,
    #  10: 100,
    #  11: 121,
    #  12: 144,
    #  13: 169,
    #  14: 196,
    #  15: 225,
    #  16: 256,
    #  17: 289,
    #  18: 324,
    #  19: 361,
    #  'not_a_cucumber': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    #  (1, 2, 3): ['key', "isn't", 'a', 'string']}

conn.close()
```
