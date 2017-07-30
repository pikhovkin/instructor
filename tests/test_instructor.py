import struct
from unittest import TestCase
import binascii

from instructor import model as instructor_model
from instructor import fields as instructor_fields
from instructor import errors as instructor_errors


class InstructorTest(TestCase):
    def test_simple_test(self):
        class Protocol(instructor_model.InstructorModel):
            byte_order = instructor_fields.NetworkByteOrder()
            protocol = instructor_fields.UInt16(default=1)
            length = instructor_fields.UInt32(default=0)
            name = instructor_fields.Str(length)

        data = '\x00\x01\x00\x00\x00\x0c\x48\x65\x6c\x6c\x6f\x20\x57\x6f\x72\x6c\x64\x21'
        p1 = Protocol(data)

        name = 'Hello World!'
        p2 = Protocol(length=len(name), name=name)

        self.assertTrue(p1.protocol == p2.protocol)
        self.assertTrue(p1.length == p2.length)
        self.assertTrue(p1.name == p2.name)

        self.assertTrue(data == p2.pack())

    def test_memcached_protocol(self):
        class MemcachedProtocol(instructor_model.InstructorModel):
            byte_order = instructor_fields.NetworkByteOrder()
            magic = instructor_fields.UInt8()
            opcode = instructor_fields.UInt8()
            key_length = instructor_fields.UInt16()
            ext_length = instructor_fields.UInt8()
            data_type = instructor_fields.UInt8()
            status = instructor_fields.UInt16()
            body_length = instructor_fields.ULong32()
            opaque = instructor_fields.ULong32()
            cas = instructor_fields.UInt64()

        package = '\x81\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00c'

        p = MemcachedProtocol(package)
        self.assertTrue(p.magic == 129)
        self.assertTrue(package == p.pack())

        p.magic = 123
        self.assertTrue(p.magic == 123)

        package2 = p.pack()
        self.assertTrue(package2 != package)

        p = MemcachedProtocol(package2)
        self.assertTrue(p.magic == 123)
        self.assertTrue(package2 == p.pack())

    def test_protocol_str_field_size_is_defined(self):
        class Protocol(instructor_model.InstructorModel):
            byte_order = instructor_fields.BigEndianByteOrder()
            protocol = instructor_fields.UInt16()
            received_status = instructor_fields.UInt8()
            urgency = instructor_fields.UInt8()
            data = instructor_fields.Str(8)

        protocol = 6
        received_status = 3
        urgency = 1
        data = '01234567'

        package = struct.pack('>HBB8s', protocol, received_status, urgency, data)

        p = Protocol(package)
        self.assertTrue(p.protocol == protocol)
        self.assertTrue(p.received_status == received_status)
        self.assertTrue(p.urgency == urgency)
        self.assertTrue(p.data == data)

        self.assertTrue(p.pack() == package)

    def test_protocol_str_field_length_depended_from_other_field(self):
        class Protocol(instructor_model.InstructorModel):
            byte_order = instructor_fields.BigEndianByteOrder()
            protocol = instructor_fields.UInt16(default=7)
            received_status = instructor_fields.UInt8(default=0)
            urgency = instructor_fields.UInt8(default=0)
            msglen = instructor_fields.UInt32(default=0)
            data = instructor_fields.Str(msglen, default='')

        protocol = 7
        received_status = 3
        urgency = 1
        data = '''test text
        '''
        msglen = len(data)

        fmt = '>HBBI{}s'.format(msglen)

        package = struct.pack(fmt, protocol, received_status, urgency, msglen, data)

        p = Protocol(package)
        self.assertTrue(p.protocol == protocol)
        self.assertTrue(p.received_status == received_status)
        self.assertTrue(p.urgency == urgency)
        self.assertTrue(p.msglen == msglen)
        self.assertTrue(p.data == data)

        self.assertTrue(p.pack() == package)

    def test_protocol_field_with_default_value(self):
        class Protocol(instructor_model.InstructorModel):
            byte_order = instructor_fields.BigEndianByteOrder()
            protocol = instructor_fields.UInt16(default=8)

        protocol = 8
        received_status = 3
        urgency = 1
        data = '01234567'

        package = struct.pack('>HBB8s', protocol, received_status, urgency, data)

        p = Protocol(package)
        self.assertTrue(p.protocol == protocol)
        with self.assertRaises(AttributeError):
            self.assertTrue(p.received_status == received_status)

        self.assertTrue(p.pack() != package)
        self.assertTrue(package.startswith(p.pack()))

    def test_instances_of_two_protocols(self):
        class Protocol(instructor_model.InstructorModel):
            byte_order = instructor_fields.BigEndianByteOrder()
            protocol = instructor_fields.UInt16(default=7)
            received_status = instructor_fields.UInt8(default=0)
            urgency = instructor_fields.UInt8(default=0)
            msglen = instructor_fields.UInt32(default=0)
            data = instructor_fields.Str(msglen, default='')

        data1 = 'test data'
        msglen1 = len(data1)
        p1 = Protocol(data=data1, msglen=msglen1)
        self.assertTrue(p1.protocol == 7)
        self.assertTrue(p1.received_status == 0)
        self.assertTrue(p1.urgency == 0)
        self.assertTrue(p1.msglen == msglen1)
        self.assertTrue(p1.data == data1)

        self.assertTrue(p1.pack())

        protocol2 = 7
        data2 = 'test'
        msglen2 = len(data2)
        p2 = Protocol(data=data2, msglen=msglen2, protocol=protocol2)
        self.assertTrue(p2.protocol == protocol2)
        self.assertTrue(p2.received_status == 0)
        self.assertTrue(p2.urgency == 0)
        self.assertTrue(p2.msglen == msglen2)
        self.assertTrue(p2.data == data2)

        self.assertTrue(p1.data != p2.data)

        self.assertTrue(p2.pack())

    def test_protocol_creation_str_length_is_defined(self):
        protocol = 9
        name = '0123456789'
        length = 5

        fields = {
            'byte_order': instructor_fields.NetworkByteOrder(),
            'protocol': instructor_fields.UInt16(default=protocol),
            'name': instructor_fields.Str(length)
        }
        Protocol = type('BaseProtocol', (instructor_model.InstructorModel,), fields)

        package = struct.pack('>H{}s'.format(length), protocol, name.encode('utf-8'))

        p = Protocol(package)
        self.assertTrue(p.protocol == protocol)
        self.assertTrue(p.name.decode('utf-8') == name[:length])

        self.assertTrue(p.pack() == package)

    def test_protocol_creation_str_length_depended_as_str(self):
        protocol = 9
        length = 5
        name = '0123456789'

        fields = {
            'byte_order': instructor_fields.NetworkByteOrder(),
            'protocol': instructor_fields.UInt16(default=protocol),
            'length': instructor_fields.UInt32(default=length),
            'name': instructor_fields.Str('length')
        }
        Protocol = type('BaseProtocol', (instructor_model.InstructorModel,), fields)

        package = struct.pack('>HI{}s'.format(length), protocol, length, name)

        p = Protocol(package)
        self.assertTrue(p.protocol == protocol)
        self.assertTrue(p.length == length)
        self.assertTrue(p.name == name[:length])

        self.assertTrue(p.pack() == package)

    def test_protocol_creation_str_length_depended_as_field(self):
        protocol = 9
        length = 5
        name = '0123456789'

        # Fields must be created in order
        fields = {
            'byte_order': instructor_fields.NetworkByteOrder(),
            'protocol': instructor_fields.UInt16(default=protocol)
        }
        fields['length'] = instructor_fields.UInt32(default=length)
        fields['name'] = instructor_fields.Str(fields['length'])

        Protocol = type('BaseProtocol', (instructor_model.InstructorModel,), fields)

        package = struct.pack('>HI{}s'.format(length), protocol, length, name)

        p = Protocol(package)
        self.assertTrue(p.protocol == protocol)
        self.assertTrue(p.length == length)
        self.assertTrue(p.name == name[:length])

        self.assertTrue(p.pack() == package)

    def test_protocol_InvalidDataSize_size_too_long(self):
        proto = 9
        str_length = 5
        name = '0123456789'

        class Protocol(instructor_model.InstructorModel):
            byte_order = instructor_fields.NetworkByteOrder()
            protocol = instructor_fields.UInt16(default=proto)
            length = instructor_fields.UInt32(default=str_length)
            name = instructor_fields.Str(length)

        package = struct.pack('>Hi{}s'.format(str_length), proto, -str_length, name)

        with self.assertRaises(instructor_errors.InvalidDataSize):
            Protocol(package)

    def test_protocol_InvalidDataSize(self):
        proto = 9
        str_length = 5
        name = '0123456789'

        class Protocol(instructor_model.InstructorModel):
            byte_order = instructor_fields.NetworkByteOrder()
            protocol = instructor_fields.UInt16(default=proto)
            length = instructor_fields.UInt32(default=str_length)
            name = instructor_fields.Str('length')

        package = struct.pack('>HI{}s'.format(str_length - 1), proto, str_length, name)

        with self.assertRaises(instructor_errors.InvalidDataSize):
            Protocol(package)
