gardendb (WIP)
============== 
Simple python flat-file databases with Cucumbers: simple, version-controlled records with streamlined pickle representations.

## Example Cucumber Usage

```python
import pickle
from cucumber import *

# Test version 0.
class Test(Cucumber):
    _version = 0
    _fields = 'foo bar foobar'.split()

# Create and pickle a Test object.
old_test = Test(1, 2, 3)
old_test_pickle = pickle.dumps(old_test, 2)

# Test version 1.
class Test(Cucumber):
    _version = 1
    _fields = 'foo bar foobar new_field'.split()

# Test version 2.
class Test(Cucumber):
    _version = 2
    _fields = 'foo bar foobar new_field'.split()

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
# Test(foo=1, bar=2, foobar=4, new_field='this is a new field')
```

## Drop-in replacement for collections.namedtuple

Cucumbers are mostly interchangeably with namedtuples using the cucumber function.

There are a few differences:

* Cucumbers have nicer pickling properties :)
* The verbose flag for will instead print out a message apologizing for not being able to print the source.
* The cucumber function also accepts `version` and `migration` keyword arguments. Specifically, `rename`, `version`, and `migrations` keywords are attached to the class as `_rename`, `_version`, and `_migrations` attributes, which is how the same functionality would be achieved the normal way.
* Cucumbers are not instances of tuple, and thus can have their own user-defined methods as well as fields that aren't part of their state.

```python
# Create a Cucumber using cucumber() with the rename flag.
# Equivalent to:
# class NamedTupleCucumber(Cucumber):
#     _fields = 'a b c import is 5'
#     _rename = True
#     _version = 5
NamedTupleCucumber = cucumber('NamedTupleCucumber', 'a b c import is 5', rename=True, version=5)
print NamedTupleCucumber(*range(6))
# NamedTupleCucumber(a=0, b=1, c=2, _3=3, _4=4, _5=5)
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
