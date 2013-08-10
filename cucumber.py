try:
    import cPickles as pickle
except ImportError:
    import pickle


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
        fields of Cucumber. Also, a default doc string is generated here.
        '''
        def __new__(self, name, bases, dct):
            if name != 'Cucumber':
                if '_fields' not in dct:
                    raise AttributeError, 'expecting _fields attribute'

                # Default version and migrations dictionary.
                dct['_version'] = dct.get('_version', None)
                dct['_migrations'] = dct.get('_migrations', {})

                # Default doc string.
                arg_list = ', '.join(map(str, dct['_fields']))
                default_doc = '{name}({arg_list})'.format(**locals())
                dct['__doc__'] = dct.get('__doc__', default_doc)

            return type.__new__(self, name, bases, dct)

    def __init__(self, *args, **kwargs):
        '''Takes arguments from _fields as variable and keyword arguments.'''
        pairs = zip(self._fields, args)
        remaining_fields = self._fields[len(pairs):]
        for name, value in pairs:
            setattr(self, name, value)
        for name, value in kwargs.items():
            remaining_fields.remove(key)
            setattr(self, name, value)
        assert not remaining_fields, \
                'No values were provided for: %r' % remaining_fields

    @classmethod
    def migrate_from(cls, old_version, new_version):
        def migration(func):
            cls._add_migration(old_version, new_version, func)
            return func
        return migration

    @classmethod
    def _add_migration(cls, old_version, new_version, func):
        for (old, new), other_func in cls._migrations.items():
            if new == old_version:
                composed = lambda *args: func(*other_func(*args))
                cls._add_migration(old, new_version, composed)
        cls._migrations[old_version, new_version] = func

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

    def __iter__(self):
        return iter(map(self.__getattribute__, self._fields))

    def __repr__(self):
        name = self.__class__.__name__
        fields = map(self.__getattribute__, self._fields)
        pairs = ('%s=%r' % pair for pair in zip(self._fields, fields))
        return '%s(%s)' % (name, ', '.join(pairs))

    def __conform__(self, protocol):
        import psycopg2
        if protocol == psycopg2.ISQLQuote:
            return self

    def getquoted(self):
        return pickle.pickle(self)
