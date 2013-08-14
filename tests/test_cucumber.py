import operator
import pickle
import StringIO
import sys

from gardendb import cucumber


Test = cucumber('Test', 'foo bar foobar')
swapped = None

def swap(x=None):
    '''Swap out Test with something else. Unswaps if x is none.'''
    global Test, swapped
    if x is None:
        Test = swapped
    else:
        Test, swapped = x, Test


def test_swap():
    MyTest = cucumber('Test', 'a b c')
    swap(MyTest)
    assert list(Test._fields) == 'a b c'.split()
    swap()
    assert list(Test._fields) == 'foo bar foobar'.split()

def test_constructor():
    assert (1, 2, 3) == Test(1, 2, 3)
    assert (1, 2, 3) == Test(1, 2, foobar=3)
    assert (1, 2, 3) == Test(1, bar=2, foobar=3)
    assert (1, 2, 3) == Test(1, foobar=3, bar=2)
    assert (1, 2, 3) == Test(foobar=3, foo=1, bar=2)
    try: Test(2, 3, foo=1)
    except TypeError: pass # expecting foobar
    else: assert False
    try: Test(1, 2, foo=1, foobar=3)
    except TypeError: pass # duplicate argument
    else: assert False

def test_migration_argument():
    X = cucumber('X', 'a b c', migrations={
        (0, 1): None,
        (1, 2): None,
        (2, 3): None,
        })
    expected = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]
    Y = cucumber('Y', 'a b c')
    Y.migrate_from(0, 1)(None)
    Y.migrate_from(1, 2)(None)
    Y.migrate_from(2, 3)(None)
    assert set(Y._migrations.keys()) == set(expected)

def test_migrations():
    old_test = Test(1, 2, 3)
    old_test_pickle = pickle.dumps(old_test, pickle.HIGHEST_PROTOCOL)
    Test2 = cucumber('Test', 'foo bar foobar new_field', version=2)
    swap(Test2)
    @Test.migrate_from(0, 1)
    def add_new_field(foo, bar, foobar):
        return (foo, bar, foobar, 'this is a new field')
    @Test.migrate_from(1, 2)
    def increment_foobar(foo, bar, foobar, new_field):
        return (foo, bar, foobar + 1, new_field)
    migrated_test = pickle.loads(old_test_pickle)
    swap()
    assert migrated_test == (1, 2, 4, 'this is a new field')

def test_verbose():
    old_test = globals()['Test'](1, 2, 3)
    old_test_pickle = pickle.dumps(old_test, 2)
    def add_new_field(foo, bar, foobar):
        return (foo, bar, foobar, 'this is a new field')
    def increment_foobar(foo, bar, foobar, new_field):
        return (foo, bar, foobar + 1, new_field)
    # Replace stdout with StringIO.
    sys.stdout = StringIO.StringIO()
    # Create verbose output.
    _Test = cucumber( 'Test'
                    , 'foo bar foobar new_field'
                    , verbose=True
                    , version=2
                    , migrations={(0, 1): add_new_field
                                 ,(1, 2): increment_foobar}
                    )
    # Get the output and restore stdout.
    verbose_output = sys.stdout.getvalue()
    sys.stdout = sys.__stdout__
    # Some renaming for namedtuple.
    namespace = {
        'add_new_field': add_new_field,
        'increment_foobar': increment_foobar,
        '_property': property,
        '_itemgetter': operator.itemgetter,
    }
    # Execute the source.
    exec verbose_output in namespace
    swap(namespace['Test'])
    # Demonstrate that evaluating the verbose output works correctly.
    migrated_test = pickle.loads(old_test_pickle)
    swap()
    assert migrated_test == (1, 2, 4, 'this is a new field')
