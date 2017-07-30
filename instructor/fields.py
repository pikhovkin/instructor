import struct


class NOT_PROVIDED:
    pass


class Dependency(object):
    def __init__(self):
        self.field = None

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return self.field if isinstance(self.field, str) else self.field.name

    def __set__(self, instance, field):
        self.field = field


class BaseFieldInstructor(object):
    _order_counter = 0
    format = None

    def __init__(self, name=None, default=NOT_PROVIDED, validators=None, choices=None, parent=None):
        self._order_counter = BaseFieldInstructor._order_counter
        BaseFieldInstructor._order_counter += 1

        self.name = name
        self.parent = parent
        self.default = default
        self.choices = choices
        self.validators = validators
        self._size = struct.calcsize(self.format)

    def has_default(self):
        return self.default is not NOT_PROVIDED

    def get_default(self):
        if self.has_default():
            if callable(self.default):
                return self.default()

            return self.default

        return None

    @property
    def size(self):
        return self._size

    def _unpack(self, instance, byte_order, data, offset=0):
        fmt = '{}{}'.format(byte_order.format, self.format)
        _value = struct.unpack_from(fmt, data, offset=offset)[0]
        return _value, self.size

    def _pack(self, instance, byte_order):
        fmt = '{}{}'.format(byte_order.format, self.format)
        data = struct.pack(fmt, getattr(instance, self.name, self.get_default()))
        return fmt, data
    

class DefaultByteOrder(BaseFieldInstructor):
    format = '@'


class NativeByteOrder(DefaultByteOrder):
    format = '='


class LitteEndianByteOrder(DefaultByteOrder):
    format = '<'


class BigEndianByteOrder(DefaultByteOrder):
    format = '>'


class NetworkByteOrder(DefaultByteOrder):
    format = '!'


class Char(BaseFieldInstructor):
    format = 'c'


class Int8(BaseFieldInstructor):
    format = 'b'


class UInt8(BaseFieldInstructor):
    format = 'B'


class Bool(BaseFieldInstructor):
    format = '?'


class Int16(BaseFieldInstructor):
    format = 'h'


class UInt16(BaseFieldInstructor):
    format = 'H'


class Int32(BaseFieldInstructor):
    format = 'i'


class UInt32(BaseFieldInstructor):
    format = 'I'


class Long32(BaseFieldInstructor):
    format = 'l'


class ULong32(BaseFieldInstructor):
    format = 'L'


class Int64(BaseFieldInstructor):
    format = 'q'


class UInt64(BaseFieldInstructor):
    format = 'Q'


class Float(BaseFieldInstructor):
    format = 'f'


class Double(BaseFieldInstructor):
    format = 'd'


class Str(BaseFieldInstructor):
    format = 's'
    _dependency = Dependency()
    _size = None

    def __init__(self, dependency_or_size, **kwargs):
        super(Str, self).__init__(**kwargs)

        if isinstance(dependency_or_size, int):
            self._dependency = None
            self._size = dependency_or_size
        else:
            self._dependency = dependency_or_size
            self._size = None

    def _unpack(self, instance, byte_order, data, offset=0):
        if self.size is not None:
            size = self.size
        else:
            size = getattr(instance, self._dependency, 0)

        fmt = '{}{}{}'.format(byte_order.format, size, self.format)
        value = struct.unpack_from(fmt, data, offset=offset)[0]

        return value, size

    def _pack(self, instance, byte_order):
        if self.size is not None:
            size = self.size
        else:
            size = getattr(instance, self._dependency, 0)

        fmt = '{}{}{}'.format(byte_order.format, size, self.format)
        return fmt, struct.pack(fmt, getattr(instance, self.name))
