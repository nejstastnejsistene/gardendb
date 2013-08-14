import collections
import inspect


def cucumber(typename, field_names, verbose=False, rename=False,
             version=0, migrations=None):
    '''Like namedtuple, but better for making pickles.'''

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

    def __new__(cls, *args, **kwargs):
        '''{cls.__new__.__doc__}

           When only one argument is provided, use that argument as
           the state for restoring from a pickled representation.
        '''.format(cls=cls)

        # Cucumbers with only one field are forbidden to avoid confusion here.
        if len(args) == 1 and not kwargs:
            version, args = args[0][0], args[0][1:]
            # Perform a migration if needed.
            if version != cls._version:
                args = cls._migrations[version, cls._version](*args)

        # Figure out args and kwargs.
        args = list(args)
        for field in cls._fields[len(args):]:
            if field not in kwargs:
                raise TypeError, 'expecting argument {!r}'.format(field)
            args.append(kwargs.pop(field))

        if kwargs:
            args = ', '.join(repr(name) for name in kwargs)
            raise TypeError, 'unexpected arguments: {!s}'.format(args)

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
        print '    _cucumber = True'
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
    cls._cucumber      = True
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


class BaseGarden(object):
    '''A place to store your cucumbers.'''

    def __init__(self, cls=None):
        self.cls = cls
        self.typed = cls is not None
        if self.typed and not issubclass(cls, tuple):
            raise ValueError, 'cls must be a subclass of tuple'

    def pack_state(self, obj):
        '''Determine an objects state to be stored.

           Must be called on values before being stored in order
           to handle typed Gardens.
        '''
        if not self.typed:
            return obj
        else:
            if obj.__class__ != self.cls:
                mesg = "value's class is not equal to {}"
                raise TypeError, mesg.format(self.cls.__name__)
            state = obj.__getnewargs__()
            if hasattr(obj.__class__, '_cucumber'):
                # Save space for cucumbers by unpacking the singleton tuple.
                state = state[0]
            return state

    def unpack_state(self, state):
        '''Unpack a object's stored state into a Python value.

           Must be called on retrieved values to handle typed Gardens.
        '''
        if not self.typed:
            return state
        else:
            if hasattr(self.cls, '_cucumber'):
                # Put the cucumber state back in a singleton tuple.
                state = (state,)
            return self.cls(*state)
