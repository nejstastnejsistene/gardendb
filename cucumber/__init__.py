from keyword import iskeyword as _iskeyword

__all__ = ('Cucumber', 'cucumber')

def cucumber(typename, field_names, verbose=False, rename=False,
             version=None, migrations={}):
    '''Create a Cucumber dynamically.

       This has the same signature as collections.namedtuple and is
       intended as a drop in replacement. It also accepts version and
       migrations keyword arguments.
    '''
    return type(typename, (Cucumber,), {
            '_fields': field_names,
            '_verbose': verbose,
            '_rename': rename,
            '_version': version,
            '_migrations': migrations,
        })


def validate_names(typename, field_names, rename):
    '''Copied from collection.py lines 311-344.'''
    # Validate the field names.  At the user's option, either generate an error
    # message or automatically replace the field name with a valid name.
    if isinstance(field_names, basestring):
        field_names = field_names.replace(',', ' ').split()
    field_names = map(str, field_names)
    if rename:
        seen = set()
        for index, name in enumerate(field_names):
            if (not all(c.isalnum() or c=='_' for c in name)
                or _iskeyword(name)
                or not name
                or name[0].isdigit()
                or name.startswith('_')
                or name in seen):
                field_names[index] = '_%d' % index
            seen.add(name)
    for name in [typename] + field_names:
        if not all(c.isalnum() or c=='_' for c in name):
            raise ValueError('Type names and field names can only contain '
                             'alphanumeric characters and underscores: %r' % name)
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a '
                             'keyword: %r' % name)
        if name[0].isdigit():
            raise ValueError('Type names and field names cannot start with '
                             'a number: %r' % name)
    seen = set()
    for name in field_names:
        if name.startswith('_') and not rename:
            raise ValueError('Field names cannot start with an underscore: '
                             '%r' % name)
        if name in seen:
            raise ValueError('Encountered duplicate field name: %r' % name)
        seen.add(name)
    return field_names


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

                # Validate the type and field names.
                dct['_fields'] = validate_names(name, dct['_fields'],
                                                dct.pop('_rename', False))

                if dct.pop('_verbose', False):
                    print 'sorry, cucumber has no verbose mode'

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
            remaining_fields.remove(name)
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
        return tuple([self._version] + list(self))

    def __setstate__(self, state):
        version = state[0]
        state = state[1:]
        if version != self._version:
            state = self._migrations[version, self._version](*state)
        for k, v in zip(self._fields, state):
            setattr(self, k, v)

    def __iter__(self):
        return iter(map(self.__getattribute__, self._fields))

    def __getitem__(self, key):
        return tuple(self)[key]

    def __repr__(self):
        name = self.__class__.__name__
        pairs = ('%s=%r' % pair for pair in zip(self._fields, self))
        return '%s(%s)' % (name, ', '.join(pairs))
