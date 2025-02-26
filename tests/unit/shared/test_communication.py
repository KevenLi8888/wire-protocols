import pytest
import json
import struct
import logging
from shared.communication import CommunicationInterface
from shared.message_format import CREATE_ACCOUNT_REQUEST, CODEMSG_RESPONSE
from shared.wire_protocol import WireProtocol

@pytest.fixture
def mock_logger():
    return logging.getLogger("test_logger")

def test_json_protocol_send(mock_socket, mock_logger):
    """Test sending data using JSON protocol format"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    test_data = {"username": "test", "password": "123"}
    
    # Create a bytearray to store sent data
    sent_buffer = bytearray()
    def mock_sendall(data):
        sent_buffer.extend(data)
    mock_socket.sendall = mock_sendall
    
    comm.send(1, test_data, mock_socket)
    
    # Verify the sent data format
    length_prefix = sent_buffer[:4]
    message = sent_buffer[4:]
    
    assert struct.unpack('!I', length_prefix)[0] == len(message)
    parsed_message = json.loads(message.decode('utf-8'))
    assert parsed_message['type'] == 1
    assert parsed_message['data'] == test_data

def test_json_protocol_receive(mock_socket, mock_logger):
    """Test receiving data using JSON protocol format"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    test_data = {"username": "test", "password": "123"}
    message = json.dumps({'type': 1, 'data': test_data}).encode('utf-8')
    
    # Prepare mock socket with test data
    length_prefix = struct.pack('!I', len(message))
    mock_socket.received_data = [length_prefix, message]
    
    # Mock the recv method to return data from received_data
    received_data_index = 0
    def mock_recv(n):
        nonlocal received_data_index
        if received_data_index >= len(mock_socket.received_data):
            return None
        data = mock_socket.received_data[received_data_index]
        received_data_index += 1
        return data
    
    mock_socket.recv = mock_recv
    
    received_data, msg_type = comm.receive(mock_socket)
    
    assert msg_type == 1
    assert received_data == test_data

def test_wire_protocol_send(mock_socket, mock_logger):
    """Test sending data using wire protocol format"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    test_data = {
        "email": "test@example.com",
        "username": "test",
        "password": "123"
    }
    
    # Create a bytearray to store sent data
    sent_buffer = bytearray()
    def mock_sendall(data):
        sent_buffer.extend(data)
    mock_socket.sendall = mock_sendall
    
    comm.send(1, test_data, mock_socket)
    
    # Verify that data was actually sent
    assert len(sent_buffer) > 0
    
    # Optional: Verify the wire protocol format
    version, msg_type, length = WireProtocol.parse_header(sent_buffer[:7])  # Changed from 5 to 7 to match HEADER_SIZE
    assert msg_type == 1
    assert length == len(sent_buffer[7:])

def test_wire_protocol_receive(mock_socket, mock_logger):
    """Test receiving data using wire protocol format"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    test_data = {
        "code": 200,
        "message": "Success"
    }
    
    # Create wire protocol message
    message = CODEMSG_RESPONSE.pack(test_data)
    header = WireProtocol.create_header(message_type=2, length=len(message))
    
    # Prepare mock socket with test data
    mock_socket.received_data = [header, message]
    
    # Mock the recv method to return data from received_data
    received_data_index = 0
    def mock_recv(n):
        nonlocal received_data_index
        if received_data_index >= len(mock_socket.received_data):
            return None
        data = mock_socket.received_data[received_data_index]
        received_data_index += 1
        return data
    
    mock_socket.recv = mock_recv
    
    received_data, msg_type = comm.receive(mock_socket)
    
    assert msg_type == 2
    assert received_data['code'] == test_data['code']
    assert received_data['message'] == test_data['message']

def test_json_protocol_receive_empty_data(mock_socket, mock_logger):
    """Test receiving empty data with JSON protocol"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    mock_socket.received_data = [None]  # Simulate EOF
    
    received_data, msg_type = comm.receive(mock_socket)
    
    assert msg_type == -1
    assert received_data == {}

def test_json_protocol_receive_invalid_json(mock_socket, mock_logger):
    """Test receiving invalid JSON data"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    invalid_message = b"invalid json"
    length_prefix = struct.pack('!I', len(invalid_message))
    mock_socket.received_data = [length_prefix, invalid_message]
    
    received_data, msg_type = comm.receive(mock_socket)
    
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_receive_empty_data(mock_socket, mock_logger):
    """Test receiving empty data with wire protocol"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    mock_socket.received_data = [None]  # Simulate EOF
    
    received_data, msg_type = comm.receive(mock_socket)
    
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_receive_invalid_data(mock_socket, mock_logger):
    """Test receiving invalid data with wire protocol"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    invalid_header = b"12345"  # Invalid header data
    mock_socket.received_data = [invalid_header, b"invalid body"]
    
    received_data, msg_type = comm.receive(mock_socket)
    
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_receive_empty_body(mock_socket, mock_logger):
    """Test receiving empty message body with wire protocol"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    header = WireProtocol.create_header(message_type=2, length=10)
    mock_socket.received_data = [header, None]  # Body is None (EOF)
    
    received_data, msg_type = comm.receive(mock_socket)
    
    assert msg_type == -1
    assert received_data == {}

def test_json_protocol_send_socket_error(mock_socket, mock_logger):
    """Test sending data when socket raises an error"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    test_data = {"username": "test"}
    
    # Make socket.getpeername() raise an error
    mock_socket.getpeername = lambda: None
    
    # Should not raise exception, just log the error
    comm.send(1, test_data, mock_socket)

def test_json_protocol_receive_socket_error(mock_socket, mock_logger):
    """Test receiving data when socket.getpeername() raises an error"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    test_data = {"username": "test"}
    message = json.dumps({'type': 1, 'data': test_data}).encode('utf-8')
    
    # Prepare mock socket with test data
    length_prefix = struct.pack('!I', len(message))
    mock_socket.received_data = [length_prefix, message]
    
    # Mock the recv method to return data from received_data
    received_data_index = 0
    def mock_recv(n):
        nonlocal received_data_index
        if received_data_index >= len(mock_socket.received_data):
            return None
        data = mock_socket.received_data[received_data_index]
        received_data_index += 1
        return data
    
    mock_socket.recv = mock_recv
    
    # Make socket.getpeername() raise an error
    mock_socket.getpeername = lambda: None
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == 1
    assert received_data == test_data

def test_wire_protocol_receive_invalid_message_type(mock_socket, mock_logger):
    """Test receiving wire protocol message with invalid message type"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    
    # Create header with invalid message type
    invalid_type = 999  # Message type that doesn't exist in MESSAGE_FORMATS
    header = WireProtocol.create_header(message_type=invalid_type, length=10)
    mock_socket.received_data = [header, b"some data"]
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_send_socket_error(mock_socket, mock_logger):
    """Test sending wire protocol message when socket.getpeername() raises error"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    test_data = {
        "email": "test@example.com",
        "username": "test",
        "password": "123"
    }
    
    # Make socket.getpeername() raise an error
    mock_socket.getpeername = lambda: None
    
    # Should not raise exception, just log the error
    comm.send(1, test_data, mock_socket)

def test_json_protocol_receive_socket_error_during_recv(mock_socket, mock_logger):
    """Test JSON protocol receive when socket.recv raises an error"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    
    # Make socket.recv raise an error
    def mock_recv(n):
        raise ConnectionError("Simulated socket error")
    mock_socket.recv = mock_recv
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_receive_socket_error_during_recv(mock_socket, mock_logger):
    """Test wire protocol receive when socket.recv raises an error"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    
    # Make socket.recv raise an error
    def mock_recv(n):
        raise ConnectionError("Simulated socket error")
    mock_socket.recv = mock_recv
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_receive_general_exception(mock_socket, mock_logger):
    """Test wire protocol receive with a general exception"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    
    # Create an invalid header that will cause an exception during parsing
    mock_socket.received_data = [b"invalid", b"data"]
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_json_protocol_receive_null_message_after_length(mock_socket, mock_logger):
    """Test JSON protocol receive when message body is null after receiving length"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    
    # First send valid length prefix
    length_prefix = struct.pack('!I', 10)  # Pretend message is 10 bytes
    # But then return None for the message body
    mock_socket.received_data = [length_prefix, None]
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_receive_with_logging_error(mock_socket, mock_logger):
    """Test wire protocol receive with logging but getpeername fails"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    test_data = {
        "code": 200,
        "message": "Success"
    }
    
    # Create wire protocol message
    message = CODEMSG_RESPONSE.pack(test_data)
    header = WireProtocol.create_header(message_type=2, length=len(message))
    mock_socket.received_data = [header, message]
    
    # Mock the recv method to return data from received_data
    received_data_index = 0
    def mock_recv(n):
        nonlocal received_data_index
        if received_data_index >= len(mock_socket.received_data):
            return None
        data = mock_socket.received_data[received_data_index]
        received_data_index += 1
        return data
    
    mock_socket.recv = mock_recv
    
    # Make getpeername raise an error to trigger the except block
    def mock_getpeername():
        raise OSError("Test error")
    mock_socket.getpeername = mock_getpeername
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == 2
    assert received_data == test_data

def test_json_protocol_receive_with_logging_error(mock_socket, mock_logger):
    """Test JSON protocol receive with logging but getpeername fails"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    test_data = {"username": "test", "password": "123"}
    message = json.dumps({'type': 1, 'data': test_data}).encode('utf-8')
    
    # Prepare mock socket with test data
    length_prefix = struct.pack('!I', len(message))
    mock_socket.received_data = [length_prefix, message]
    
    # Mock the recv method to return data from received_data
    received_data_index = 0
    def mock_recv(n):
        nonlocal received_data_index
        if received_data_index >= len(mock_socket.received_data):
            return None
        data = mock_socket.received_data[received_data_index]
        received_data_index += 1
        return data
    
    mock_socket.recv = mock_recv
    
    # Make getpeername raise an error to trigger the except block
    def mock_getpeername():
        raise OSError("Test error")
    mock_socket.getpeername = mock_getpeername
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == 1
    assert received_data == test_data

def test_grpc_protocol_initialization(mock_logger):
    """Test initialization of gRPC protocol"""
    comm = CommunicationInterface(protocol_type='grpc', logger=mock_logger)
    assert comm.protocol_type == 'grpc'
    assert comm.grpc_handler is not None

def test_grpc_protocol_send_missing_client(mock_logger):
    """Test sending gRPC message without providing a client"""
    comm = CommunicationInterface(protocol_type='grpc', logger=mock_logger)
    test_data = {"username": "test"}
    
    with pytest.raises(ValueError, match="gRPC client not provided"):
        comm.send(1, test_data)

def test_grpc_protocol_send_with_client(mock_logger, mocker):
    """Test sending gRPC message with a client"""
    comm = CommunicationInterface(protocol_type='grpc', logger=mock_logger)
    test_data = {"username": "test"}
    
    # Mock the gRPC client and handler
    mock_grpc_client = mocker.Mock()
    mock_response = {"status": "success"}
    mocker.patch.object(comm.grpc_handler, 'handle_message', return_value=mock_response)
    
    response = comm.send(1, test_data, grpc_client=mock_grpc_client)
    
    # Verify the handler was called with correct arguments
    comm.grpc_handler.handle_message.assert_called_once_with(1, test_data, mock_grpc_client)
    assert response == mock_response

def test_json_protocol_send_exception(mock_socket, mock_logger):
    """Test exception handling when sending JSON protocol message"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    test_data = {"username": "test"}
    
    # Make sendall raise an exception
    def mock_sendall(data):
        raise ConnectionError("Simulated connection error")
    mock_socket.sendall = mock_sendall
    
    with pytest.raises(ConnectionError):
        comm.send(1, test_data, mock_socket)

def test_wire_protocol_send_exception(mock_socket, mock_logger):
    """Test exception handling when sending wire protocol message"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    test_data = {"username": "test", "password": "123"}
    
    # Make sendall raise an exception
    def mock_sendall(data):
        raise ConnectionError("Simulated connection error")
    mock_socket.sendall = mock_sendall
    
    with pytest.raises(ConnectionError):
        comm.send(1, test_data, mock_socket)

def test_json_protocol_receive_partial_length(mock_socket, mock_logger):
    """Test JSON protocol receive with partial length prefix"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    
    # Mock recv to return partial data then None (connection closed)
    call_count = 0
    def mock_recv(n):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return b'\x00\x00'  # Partial length prefix
        return None  # Connection closed
    mock_socket.recv = mock_recv
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_json_protocol_receive_partial_message(mock_socket, mock_logger):
    """Test JSON protocol receive with partial message body"""
    comm = CommunicationInterface(protocol_type='json', logger=mock_logger)
    
    # First return valid length prefix for a 10-byte message
    length_prefix = struct.pack('!I', 10)
    
    # Then return partial message followed by None (connection closed)
    call_count = 0
    def mock_recv(n):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return length_prefix
        if call_count == 2:
            return b'{"type":1'  # Partial JSON
        return None  # Connection closed
    mock_socket.recv = mock_recv
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_receive_partial_header(mock_socket, mock_logger):
    """Test wire protocol receive with partial header"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    
    # Mock recv to return partial header then None (connection closed)
    call_count = 0
    def mock_recv(n):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return b'\x01\x02\x03'  # Partial header (less than HEADER_SIZE)
        return None  # Connection closed
    mock_socket.recv = mock_recv
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_wire_protocol_receive_partial_body(mock_socket, mock_logger):
    """Test wire protocol receive with partial message body"""
    comm = CommunicationInterface(protocol_type='wire', logger=mock_logger)
    
    # Create a valid header for a message with length 10
    header = WireProtocol.create_header(message_type=2, length=10)
    
    # Mock recv to return valid header but partial body
    call_count = 0
    def mock_recv(n):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return header
        if call_count == 2:
            return b'partial'  # Partial body (less than expected length)
        return None  # Connection closed
    mock_socket.recv = mock_recv
    
    received_data, msg_type = comm.receive(mock_socket)
    assert msg_type == -1
    assert received_data == {}

def test_grpc_protocol_send_exception(mock_logger, mocker):
    """Test exception handling when sending gRPC message"""
    # Create a mock logger instead of using the fixture
    mock_logger = mocker.Mock()
    comm = CommunicationInterface(protocol_type='grpc', logger=mock_logger)
    test_data = {"username": "test"}
    
    # Mock the gRPC handler to raise an exception
    mock_grpc_client = mocker.Mock()
    mocker.patch.object(comm.grpc_handler, 'handle_message', 
                        side_effect=Exception("Simulated gRPC error"))
    
    # Test that the exception is re-raised
    with pytest.raises(Exception):
        comm.send(1, test_data, grpc_client=mock_grpc_client)
    
    # Verify the logger was called with an error message
    mock_logger.error.assert_called()

def test_grpc_protocol_send_without_logger(mocker):
    """Test sending gRPC message without a logger"""
    comm = CommunicationInterface(protocol_type='grpc', logger=None)
    test_data = {"username": "test"}
    
    # Mock the gRPC handler to raise an exception
    mock_grpc_client = mocker.Mock()
    mocker.patch.object(comm.grpc_handler, 'handle_message', 
                        side_effect=Exception("Simulated gRPC error"))
    
    # Test that the exception is re-raised even without a logger
    with pytest.raises(Exception):
        comm.send(1, test_data, grpc_client=mock_grpc_client)

def test_grpc_protocol_send_debug_logging(mock_logger, mocker):
    """Test debug logging when sending gRPC message"""
    # Create a mock logger instead of using the fixture
    mock_logger = mocker.Mock()
    comm = CommunicationInterface(protocol_type='grpc', logger=mock_logger)
    test_data = {"username": "test"}
    
    # Mock the gRPC client and handler
    mock_grpc_client = mocker.Mock()
    mock_response = {"status": "success"}
    mocker.patch.object(comm.grpc_handler, 'handle_message', return_value=mock_response)
    
    comm.send(1, test_data, grpc_client=mock_grpc_client)
    
    # Verify debug logging was called
    mock_logger.debug.assert_called_with(f"Sending gRPC message type 1: {test_data}") 