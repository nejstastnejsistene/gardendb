from keyword import iskeyword as _iskeyword
import collections
import inspect

__all__ = ('Cucumber', 'cucumber')


def cucumber(typename, field_names, verbose=False, rename=False,
             version=None, migrations=None):
    if migrations is None:
        migrations = {}

    # Convert field_names early to detect length.
    if isinstance(field_names, basestring):
        field_names = field_names.replace(',', '').split()

    # Require at least two fields to avoid confusion during unpickling.
    if len(field_names) == 1:
        raise ValueError, 'cucumbers must have at least 2 fields'

    # Start out with a namedtuple.
    cls = collections.namedtuple(typename, field_names, verbose, rename)

    def __getnewargs__(self):
        '''A singleton tuple containing the version and arguments.
        
           This overrides namedtuple's __getnewargs__().
        '''
        return (tuple([self._version] + list(self)),)

    def __new__(cls, *args):
        '''{cls.__new__.__doc__}

           When only one argument is provided, use that argument as
           the state for restoring from a pickled representation.
        '''.format(cls=cls)
        # Cucumbers with only one field are forbidden to avoid confusion here.
        if len(args) == 1:
            version, args = args[0][0], args[0][1:]
            # Perform a migration if needed.
            if version != cls._version:
                args = cls._migrations[version, cls._version](*args)
        return tuple.__new__(cls, args)

    def __getstate__(self):
        '''Minimize pickle size by excluding state.'''

    def __setstate__(self):
        '''Minimize pickle size by excluding state.'''

    def migrate_from(cls, old_version, new_version):
        '''Decorator for defining migrations between versions.'''
        def migration(func):
            cls._add_migration(old_version, new_version, func)
            return func
        return migration

    def _add_migration(cls, old_version, new_version, func):
        '''Add a migration.'''
        for (old, new), other_func in cls._migrations.items():
            if new == old_version:
                composed = lambda *args: func(*other_func(*args))
                cls._add_migration(old, new_version, composed)
        cls._migrations[old_version, new_version] = func

    # Construct some source code for verbose outcode.
    if verbose:

        # Try to make verbose source code as correct as possible by
        # by removing the string formatting I used above.
        repr_new = inspect.getsource(__new__) \
                    .replace('.format(cls=cls)', '') \
                    .replace('{cls.__new__.__doc__}', cls.__new__.__doc__)

        print '    # The following have been added by cucumber:'
        print
        print '    _version =', repr(version)
        print '    _migrations = {}'
        print
        print inspect.getsource(__getnewargs__)
        print repr_new
        print '    @classmethod'
        print inspect.getsource(migrate_from)
        print '    @classmethod'
        print inspect.getsource(_add_migration)
        print inspect.getsource(__getstate__)
        print inspect.getsource(__setstate__)
        for k, v in migrations.items():
            fmt = '{!s}._add_migration({!r}, {!r}, {.__name__!s})'
            print fmt.format(typename, k[0], k[1], v)

    # Add new fields to the class.
    cls._version       = version
    cls._migrations    = {}
    cls.__getnewargs__ = __getnewargs__
    cls.__new__        = staticmethod(__new__)
    cls.__getstate__   = __getstate__
    cls.__setstate__   = __setstate__
    cls.migrate_from   = classmethod(migrate_from)
    cls._add_migration = classmethod(_add_migration)
    for k, v in migrations.items():
        cls._add_migration(k[0], k[1], v)

    # Correct __module__ for pickling to work correctly. 
    try:
        frame = inspect.currentframe().f_back
        cls.__module__ = frame.f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return cls


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
