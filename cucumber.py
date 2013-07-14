
class Cucumber(object):
    '''
    Lightweight pickles.

    Cucumbers are simple, version-controlled records with streamlined pickle
    representations.
    '''

    _version = None

    class __metaclass__(type):
        def __new__(self, name, bases, dct):
            if name != 'Cucumber' and '_fields' not in dct:
                raise AttributeError, 'expecting _fields attribute'
            return type.__new__(self, name, bases, dct)

    def __getstate__(self):
        fields = map(self.__getattribute__, self._fields)
        return tuple([self._version] + fields)

    def __setstate__(self, state):
        assert state[0] == self._version
        for k, v in zip(self._fields, state[1:]):
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

test = Test(1, 2, 3)
import pickle
print len(pickle.dumps(test, 2))
