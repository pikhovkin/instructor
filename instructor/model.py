from collections import OrderedDict

from .errors import InvalidData, InvalidDataSize, InvalidModelDeclaration
from .fields import BaseFieldInstructor, DefaultByteOrder


__all__ = (
    'InstructorModel',
)


class Opts(object):
    pass


class MetaInstructor(type):
    def __new__(cls, name, bases, attrs):
        declared_fields = [(key, value) for key, value in attrs.iteritems() if isinstance(value, BaseFieldInstructor)]
        _fields = OrderedDict(sorted(declared_fields, key=lambda x: x[1]._order_counter))

        if _fields and not isinstance(_fields.values()[0], DefaultByteOrder):
            raise InvalidModelDeclaration('First field of a class must be subclass of DefaultByteOrder')

        for field_name, field in _fields.iteritems():
            field.name = field_name

            attrs.pop(field_name)

        new_cls = type.__new__(cls, name, bases, attrs)
        new_cls._meta = Opts()
        new_cls._meta.fields = _fields

        for field_name, field in _fields.iteritems():
            setattr(new_cls._meta, field_name, field)

        return new_cls


class InstructorModel(object):
    __metaclass__ = MetaInstructor

    def __init__(self, *args, **kwargs):
        if args:
            data = args[0]
            offset = 0

            byte_order = self._meta.fields.values()[0]
            try:
                for i, field in enumerate(self._meta.fields.itervalues()):
                    if i == 0:
                        continue

                    value, size = field._unpack(self, byte_order, data, offset=offset)
                    offset += size
                    setattr(self, field.name, value)
            except Exception as e:
                if e.args[0] == 'total struct size too long':
                    raise InvalidDataSize(e.args[0])
                elif e.args[0].startswith('unpack_from requires a buffer of at least'):
                    raise InvalidDataSize(e.args[0])

                raise e
        elif kwargs:
            for i, field in enumerate(self._meta.fields.itervalues()):
                if i == 0:
                    continue

                value = kwargs.get(field.name, field.get_default())
                setattr(self, field.name, value)
        else:
            raise InvalidData

    @classmethod
    def unpack(cls, data):
        return cls(data)

    def pack(self):
        fmt = ''
        data = ''
        byte_order = self._meta.fields.values()[0]
        for i, field in enumerate(self._meta.fields.itervalues()):
            if i == 0:
                continue

            _fmt, _data = field._pack(self, byte_order)

            fmt += _fmt
            data += _data

        return data
