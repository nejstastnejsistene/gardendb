
class Cucumber(object):
    '''
    Lightweight pickles.

    Cucumbers are simple, version-controlled records with streamlined pickle
    representations.
    '''

    class __metaclass__(type):
        '''
        Enforce the existance of _fields, and fill in defaults for _version
        and _migrations.

        I feel justified using this "black magic" because I think it's
        important to raise an error for a missing _fields attribute early
        rather than later when trying to pickle, and to avoid weird
        name space issues from having _version and _migrations as class
        fields of Cucumber.
        '''
        def __new__(self, name, bases, dct):
            if name != 'Cucumber':
                if '_fields' not in dct:
                    raise AttributeError, 'expecting _fields attribute'
                dct['_version'] = dct.get('_version', None)
                dct['_migrations'] = dct.get('_migrations', {})
            return type.__new__(self, name, bases, dct)

    @classmethod
    def migrate_from(cls, old_version, new_version):
        def migration(func):
            cls._migrations[old_version, new_version] = func
            return func
        return migration

    def __getstate__(self):
        fields = map(self.__getattribute__, self._fields)
        return tuple([self._version] + fields)

    def __setstate__(self, state):
        version = state[0]
        state = state[1:]
        if version != self._version:
            state = self._migrations[version, self._version](*state)
        for k, v in zip(self._fields, state):
            setattr(self, k, v)

    def __repr__(self):
        name = self.__class__.__name__
        fields = map(self.__getattribute__, self._fields)
        pairs = ('%s=%r' % pair for pair in zip(self._fields, fields))
        return '%s(%s)' % (name, ', '.join(pairs))


class Test(Cucumber):
    _version = '1.0'
    _fields = 'foo bar foobar'.split()

    def __init__(self, foo, bar, foobar):
        self.foo = foo
        self.bar = bar
        self.foobar = foobar

import pickle
old_test = Test(1, 2, 3)
old_test_pickle = pickle.dumps(old_test, 2)
print len(old_test_pickle)

class Test(Cucumber):
    _version = '1.1'
    _fields = 'foo bar foobar new_field'.split()

    def __init__(self, foo, bar, foobar, new_field):
        self.foo = foo
        self.bar = bar
        self.foobar = foobar
        self.new_field = new_field

@Test.migrate_from('1.0', '1.1')
def add_new_field(foo, bar, foobar):
    return (foo, bar, foobar, 'this is a new field')

migrated_test = pickle.loads(old_test_pickle)
print migrated_test
