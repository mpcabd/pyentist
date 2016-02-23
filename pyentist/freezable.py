class Freezable(object):

    def __init__(self):
        self._is_frozen = False

    def freeze(self):
        self._is_frozen = True

        for prop in dir(self.__class__):
            p = getattr(self.__class__, prop)
            if isinstance(p, property) and p.fset:
                def setter(self, *args, **kwargs):
                    raise AttributeError(
                        "Cannot set property {} of object {} because it is frozen.".format(
                            prop,
                            self
                        )
                    )
                setattr(self.__class__, prop, property(p.fget, setter, p.fdel))

    @property
    def is_frozen(self):
        if not hasattr(self, '_is_frozen'):
            self._is_frozen = False
        return self._is_frozen
