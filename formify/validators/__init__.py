import copy
import weakref

from formify import exc, event
from formify.utils import helpers
from formify.undefined import Undefined


class Validator(object):
    """Base class for all validators providing core functionality."""
    __visit_name__ = 'validator'

    def __init__(self, **kwargs):
        helpers.set_creation_order(self)

        # The purpose of this variable is to restore original validator's state
        # once validator is bound to schema
        self._bind_kwargs = dict(kwargs)

        # Read only properties
        self._key = kwargs.pop('key', None)
        self._owner = None
        self._raw_value = Undefined
        self._value = Undefined
        self._errors = []

        # Read and write properties
        self.label = kwargs.pop('label', None)
        self.default = kwargs.pop('default', Undefined)
        self.description = kwargs.pop('description', None)
        self.required = kwargs.pop('required', True)

        # Remaining custom read and write properties
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __setattr__(self, name, value):
        super(Validator, self).__setattr__(name, value)
        if not name.startswith('_'):  # Keep track of changed public properties
            self._bind_kwargs[name] = value

    def _raise_if_unbound(self, func, excs, *args, **kwargs):
        """Call given function with provided args and kwargs and return its
        value.

        If exception occurs (one of listed *excs*) do following:

        for unbound validator
            raise exception

        for bound validator
            add exception description to list of current validator's errors and
            return ``Undefined`` object

        :param func:
            function to be called
        :param excs:
            exception or tuple tuple of exceptions to be catched by
            ``try...except`` block
        :param *args:
            function's args
        :param **kwargs:
            function's named args
        """
        try:
            return func(*args, **kwargs)
        except excs, e:
            if self.is_bound():
                self.errors.append(unicode(e))
                return Undefined
            else:
                raise

    def _typecheck(self, value):
        """A helper to perform correct type checking of processed value depending on
        :attr:`multivalue` state."""
        if self.multivalue:
            for v in value:
                if not self.typecheck(v):
                    return False
            return True
        else:
            return self.typecheck(value)

    def _from_string(self, value):
        """A helper to perform correct from string conversion of processed
        value depending on :attr:`multivalue` state."""
        if self.multivalue:
            for i in xrange(len(value)):
                if isinstance(value[i], basestring):
                    value[i] = self.from_string(value[i])
            return value
        elif isinstance(value, basestring):
            return self.from_string(value)
        else:
            return value

    def is_bound(self):
        """Check if this validator is bound."""
        return self._owner is not None

    @staticmethod
    def has_bound_validators(owner):
        """Check if given *owner* has validators bound to it."""
        return hasattr(owner, '_bound_validators')

    @staticmethod
    def is_bound_to(owner, key):
        """Check if *key* is a key of validator bound to *owner*.

        This method assumes that *owner* has at least one validator bound. Use
        :meth:`has_bound_validators` to check such condition.

        :param owner:
            bound validator's owner
        :param key:
            bound validator's key
        """
        return key in owner._bound_validators

    @staticmethod
    def get_bound_validator(owner, key):
        """Return instance of bound validator."""
        return owner._bound_validators[key]

    def bind(self, owner):
        """Bind validator to given owner.

        This method returns new bound validator based on current one. Original
        validator (the one for which this method was called) remains unchanged.
        """
        if self.is_bound():
            raise exc.AlreadyBound("%r -> %r" % (self, self.owner))

        # Create bound validator instance
        # Use custom defined function to do this if registered as 'bind' event
        # listener
        binders = event.get_listeners(self, 'bind')
        if not binders:
            bound = self.__class__(**self._bind_kwargs)
        else:
            bound = binders[-1](self.owner, self.key, self.__class__, self._bind_kwargs)

        # Reset properties that cannot be modified
        bound._key = self._key
        bound._owner = weakref.ref(owner)

        # Set default value
        default = bound.default
        if default is not Undefined:
            bound.process(copy.deepcopy(default))

        # Forward all event retrieval requests to validator originally created
        # as schema attribute
        event.alias_of(bound, self, event.F_READ_ACCESS)

        # Bind newly created validator to schema and return
        if not hasattr(owner, '_bound_validators'):
            owner._bound_validators = {}
        owner._bound_validators[self._key] = bound
        return bound

    def unbind(self):
        """Unbind this validator from current owner.

        If this validator was not bound to any owner,
        :exc:`~formify.exc.NotBound` is raised.
        """
        if not self.is_bound():
            raise exc.NotBound(repr(self))
        del self.owner._bound_validators[self._key]
        self._owner = None

    def process(self, value):
        """Process value by running prevalidators, converters and
        postvalidators.

        This method returns processed value. Also, if validator is bound, it
        sets up :param:`raw_value` and :param:`value` params.
        """

        # Expect value to be a sequence and convert it to list in case of
        # multivalue validators
        if self.multivalue:
            value = list(value)

        # Initialize raw_value, value and error container
        if self.is_bound():
            self._raw_value = value
            self._value = Undefined
            self._errors = []

        # Execute only if value needs conversion
        if not self._typecheck(value):

            # Run prevalidators
            value = self._raise_if_unbound(self.prevalidate, ValueError, value)

            # Convert to valid type from string
            if value is not Undefined:
                value = self._raise_if_unbound(self._from_string, TypeError, value)

            # If value is Undefined object (f.e. there was processing error) -
            # return it to avoid TypeError being raised
            if value is Undefined:
                return Undefined

            # Raise exception if type is still invalid
            if not self._typecheck(value):
                raise TypeError(
                    "validator %r was unable to convert %r to valid type" %
                    (self, value))

        # Run postvalidators
        value = self._raise_if_unbound(self.postvalidate, ValueError, value)

        # Set up processed value
        if self.is_bound():
            self._value = value

        return value

    def prevalidate(self, value):
        """Process input value of unsupported type.

        Prevalidators are executed if *value* needs to be converted to valid
        type expected for this validator. It is expected that prevalidators
        will convert *value* either to :param:`python_type` object or to
        :class:`basestring` object.

        .. note::
            There is no need to convert strings inside prevalidators - use
            :meth:`from_string` instead.

        :param value:
            the value to be prevalidated

        :rtype: :class:`basestring` or :meth:`python_type`
        """
        return event.pipeline(self, 'prevalidate', -1, self.owner, self.key, value)

    def postvalidate(self, value):
        """Process converted value.

        This method is executed only if conversion to :param:`python_type` was
        successful.

        :param value:
            the value to be postvalidated
        """
        return event.pipeline(self, 'postvalidate', -1, self.owner, self.key, value)

    def validate(self, value):
        """Validate processed value.

        This validation process is issued once :meth:`is_valid` is called for
        this validator.
        """
        return event.pipeline(self, 'validate', -1, self.owner, self.key, value)

    def from_string(self, value):
        """Convert string value to :param:`python_type` type object.

        This method raises :exc:`~formify.exc.ConversionError` if conversion
        cannot be performed.
        """
        try:
            return self.python_type(value)
        except (ValueError, TypeError):
            raise exc.ConversionError("unable to convert '%(value)s' to desired type" % {'value': value})

    def typecheck(self, value):
        """Check if type of *value* is supported by this validator."""
        return isinstance(value, self.python_type)

    def is_valid(self):
        """Check if last value was processed successfuly."""
        if not self.is_bound():
            return True  # always valid if not bound
        elif self.errors:
            return False  # if validator already has errors, return false and skip further validation
        elif self.required and self.value is Undefined:
            self._errors.append(u'this field is required')
            return False
        self._value = self._raise_if_unbound(self.validate, ValueError, self._value)
        return len(self.errors) == 0

    def accept(self, visitor):
        """Accept given visitor by calling visit method that matches
        validator's :attr:`__visit_name__`.

        :param visitor:
            visitor object
        """
        name = "visit_%s" % self.__visit_name__
        visit = getattr(visitor, name, None)
        if visit is None:
            raise NotImplementedError(
                "the visitor %r does not have %r method" %(visitor, name))
        return visit(self)

    @property
    def key(self):
        """The key assigned to this validator."""
        return self._key

    @property
    def name(self):
        """The name of this validator.

        This is equal to validator's class name.
        """
        return self.__class__.__name__

    @property
    def namespace(self):
        """Namespace of this validator."""
        if not self.is_bound():
            return Undefined
        elif hasattr(self.owner, 'key'):
            return self.owner.key
        else:
            return ''

    @property
    def owner(self):
        """Schema object this validator is bound to or ``None`` if this
        validator is not bound to any schema."""
        if self._owner is not None:
            return self._owner()
        else:
            return None

    @property
    def raw_value(self):
        """Unchanged value :meth:`process` was called with.

        If this is ``Undefined``, :meth:`process` was not called yet or was
        called with ``Undefined`` object value.
        """
        return self._raw_value

    @property
    def value(self):
        """Output value produced by this validator.

        If this is ``Undefined``, :meth:`process` was not called yet or - if
        :param:`raw_value` is set - validator was not able to process value.
        """
        return self._value

    @property
    def errors(self):
        """List of validation errors.

        Access to this list is public - it can be modified to force validation
        errors f.e. in custom event listener callables.
        """
        return self._errors

    @property
    def python_type(self):
        """Python type object this validator converts input values to."""
        raise NotImplementedError("'python_type' is not implemented in %r" % self.__class__)

    @property
    def multivalue(self):
        """``True`` if validator is a multivalue validator (i.e. it accepts and
        validates sequence of values of same type) or ``False`` otherwise."""
        return False

    @property
    def label(self):
        """Validator's label.

        By default, this is calculated from validator's :param:`key`.
        """
        if self._label is None:
            return unicode(self.key.replace('_', ' ').capitalize())
        elif self._label is Undefined:
            return Undefined
        else:
            return unicode(self._label)

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def default(self):
        """Default value of this validator."""
        if self._default is Undefined:
            return Undefined
        else:
            return helpers.maybe_callable(self._default)

    @default.setter
    def default(self, value):
        self._default = value


# Import most commonly used validators
from formify.validators.core import (
    BaseString, String, Text, Regex, Numeric, Integer, Float, Decimal, Boolean,
    Choice)
from formify.validators.grouping import Map
