import pytest
import struct
from shared.wire_protocol import WireProtocol
from shared.message_format import MessageFormat

class TestWireProtocol:
    def test_create_header(self):
        # Test creating a header with valid inputs
        message_type = 1
        length = 100
        header = WireProtocol.create_header(message_type, length)
        
        # Verify header length and content
        assert len(header) == WireProtocol.HEADER_SIZE
        version, msg_type, body_len = struct.unpack(WireProtocol.HEADER_FORMAT, header)
        assert version == WireProtocol.VERSION
        assert msg_type == message_type
        assert body_len == length

    def test_parse_header(self):
        # Test parsing a valid header
        message_type = 2
        length = 200
        header = WireProtocol.create_header(message_type, length)
        version, msg_type, body_len = WireProtocol.parse_header(header)
        
        assert version == WireProtocol.VERSION
        assert msg_type == message_type
        assert body_len == length

    def test_marshal_with_data(self, monkeypatch):
        # Create a mock MessageFormat class
        class MockMessageFormat:
            def pack(self, data):
                return b'test_body'

        mock_format = MockMessageFormat()
        
        # Test marshaling data
        message_type = 3
        test_data = {'key': 'value'}
        result = WireProtocol.marshal(message_type, mock_format, test_data)

        # Verify the result
        header = result[:WireProtocol.HEADER_SIZE]
        body = result[WireProtocol.HEADER_SIZE:]
        
        version, msg_type, body_len = WireProtocol.parse_header(header)
        assert version == WireProtocol.VERSION
        assert msg_type == message_type
        assert body_len == len(body)
        assert body == b'test_body'

    def test_marshal_with_none_data(self, monkeypatch):
        # Create a mock MessageFormat class
        class MockMessageFormat:
            def pack(self, data):
                return b''

        mock_format = MockMessageFormat()

        # Test marshaling None data
        message_type = 4
        result = WireProtocol.marshal(message_type, mock_format, None)

        # Verify the result
        header = result[:WireProtocol.HEADER_SIZE]
        version, msg_type, body_len = WireProtocol.parse_header(header)
        assert version == WireProtocol.VERSION
        assert msg_type == message_type
        assert body_len == 0

    def test_unmarshal_with_data(self, monkeypatch):
        # Create a mock MessageFormat class
        class MockMessageFormat:
            def unpack(self, data):
                return ({'key': 'value'}, None)

        mock_format = MockMessageFormat()
        test_data = b'test_data'

        # Test unmarshaling data
        result = WireProtocol.unmarshal(mock_format, test_data)

        # Verify the result
        assert result == {'key': 'value'}

    def test_unmarshal_with_empty_data(self, monkeypatch):
        # Create a mock MessageFormat class
        class MockMessageFormat:
            def unpack(self, data):
                assert False, "unpack should not be called"

        mock_format = MockMessageFormat()

        # Test unmarshaling empty data
        result = WireProtocol.unmarshal(mock_format, b'')

        # Verify the result
        assert result == {}
