# formify/types.py
#
# Copyright (C) 2014 Maciej Wiatrzyk
#
# This module is part of Formify and is released under the MIT license:
# http://opensource.org/licenses/mit-license.php

"""Set of various types and type mixins that could be useful when defining
custom validator."""


class DictMixin(object):
    """A mixin that provides other classes with dict-like interface.

    This is very similar to :class:`UserDict.DictMixin`, but ``__iter__`` must
    be defined instead of ``keys`` and new-style class is used.
    """

    def __cmp__(self, other):
        if other is None:
            return 1
        elif hasattr(other, 'iteritems'):
            return cmp(dict(self.iteritems()), dict(other.iteritems()))
        else:
            return cmp(dict(self.iteritems()), other)

    def __len__(self):
        return len(self.keys())

    def __repr__(self):
        return repr(dict(self.iteritems()))

    def has_key(self, key):
        return key in self

    def iterkeys(self):
        for k in self:
            yield k

    def keys(self):
        return list(self.iterkeys())

    def iteritems(self):
        for k in self:
            yield k, self[k]

    def items(self):
        return list(self.iteritems())

    def itervalues(self):
        for _, v in self.iteritems():
            yield v

    def values(self):
        return list(self.itervalues())

    def clear(self):
        for k in self.keys():
            del self[k]

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def pop(self, key, *default):
        if key in self:
            value = self[key]
            del self[key]
            return value
        elif not default:
            raise KeyError(key)
        elif len(default) == 1:
            return default[0]
        else:
            raise TypeError("pop expected at most 2 arguments, got %r" % (1 + len(default)))

    def popitem(self):
        try:
            k, v = self.iteritems().next()
        except StopIteration:
            raise KeyError('container is empty')
        del self[k]
        return k, v

    def update(self, other=None, **kwargs):
        if hasattr(other, 'iteritems'):
            for k, v in other.iteritems():
                self[k] = v
        elif other is not None:
            for k, v in other:
                self[k] = v
        if kwargs:
            self.update(kwargs)

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default
