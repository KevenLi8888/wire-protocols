import unittest
from shared.wire_protocol import WireProtocol
from shared.message_format import MessageFormat, MessageField
from shared.constants import *

class TestWireProtocol(unittest.TestCase):
    def setUp(self):
        self.login_format = MessageFormat({
            'email': MessageField('email', 's'),
            'password': MessageField('password', 's')
        })

    def test_header_pack_unpack(self):
        message_type = MSG_LOGIN_REQUEST
        body_length = 100
        header = WireProtocol.create_header(message_type, body_length)
        
        # Verify header length
        self.assertEqual(len(header), WireProtocol.HEADER_SIZE)
        
        version, msg_type, length = WireProtocol.parse_header(header)
        self.assertEqual(version, WireProtocol.VERSION)
        self.assertEqual(msg_type, message_type)
        self.assertEqual(length, body_length)

    def test_marshal_unmarshal(self):
        message_type = MSG_LOGIN_REQUEST
        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        
        # Marshal the message
        wire_msg = WireProtocol.marshal(message_type, self.login_format, data)
        
        # Verify total message length
        self.assertTrue(len(wire_msg) >= WireProtocol.HEADER_SIZE)
        
        # Extract header and body
        header = wire_msg[:WireProtocol.HEADER_SIZE]
        body = wire_msg[WireProtocol.HEADER_SIZE:]
        
        # Parse header
        version, msg_type, length = WireProtocol.parse_header(header)
        
        # Verify header content
        self.assertEqual(version, WireProtocol.VERSION)
        self.assertEqual(msg_type, message_type)
        self.assertEqual(length, len(body))
        
        # Unmarshal body
        unpacked = WireProtocol.unmarshal(self.login_format, body)
        self.assertEqual(data, unpacked)

    def test_complex_message(self):
        user_format = MessageFormat({
            'id': MessageField('id', 's'),
            'name': MessageField('name', 's')
        })
        
        response_format = MessageFormat({
            'code': MessageField('code', 'i'),
            'message': MessageField('message', 's'),
            'users': MessageField('users', None, is_nested=True, is_list=True, nested_format=user_format)
        })
        
        data = {
            'code': SUCCESS,
            'message': MESSAGE_OK,
            'users': [
                {'id': '1', 'name': 'John'},
                {'id': '2', 'name': 'Jane'}
            ]
        }
        
        wire_msg = WireProtocol.marshal(MSG_GET_USERS_RESPONSE, response_format, data)
        body = wire_msg[WireProtocol.HEADER_SIZE:]
        unpacked = WireProtocol.unmarshal(response_format, body)
        self.assertEqual(data, unpacked)

if __name__ == '__main__':
    unittest.main()
