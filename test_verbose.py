import pickle
import sys
import StringIO
from gardendb import *

Test = cucumber('Test', 'foo bar foobar', version=0)

old_test = Test(1, 2, 3)
old_test_pickle = pickle.dumps(old_test, 2)

def add_new_field(foo, bar, foobar):
    return (foo, bar, foobar, 'this is a new field')

def increment_foobar(foo, bar, foobar, new_field):
    return (foo, bar, foobar + 1, new_field)

# Replace stdout with StringIO.
sys.stdout = StringIO.StringIO()

# Create verbose output.
Test = cucumber( 'Test'
               , 'foo bar foobar new_field'
               , verbose=True
               , version=2
               , migrations={(0, 1): add_new_field, (1, 2): increment_foobar}
               )

# Get the output and restore stdout.
verbose_output = sys.stdout.getvalue()
sys.stdout = sys.__stdout__

# "Hide" the original Test object.
_Test = Test
del Test

# Some renaming for namedtuple.
_property = property
from operator import itemgetter as _itemgetter

# Execute the source.
exec verbose_output in globals()

# Demonstrate that evaluating the verbose output works correctly.
migrated_test = pickle.loads(old_test_pickle)
print migrated_test
