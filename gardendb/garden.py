try:
    import cPickle
except ImportError:
    import pickle


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
