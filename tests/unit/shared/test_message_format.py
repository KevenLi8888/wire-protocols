import pytest
from shared.message_format import MessageFormat, MessageField

# Test the pack and unpack functionality of MessageFormat
# Verifies that data can be correctly serialized and deserialized
def test_message_format_pack_unpack():
    format_def = MessageFormat({
        'username': MessageField('username', 's'),
        'age': MessageField('age', 'i')
    })
    
    test_data = {
        'username': 'test_user',
        'age': 25
    }
    
    packed = format_def.pack(test_data)
    unpacked, _ = format_def.unpack(packed)
    
    assert unpacked['username'] == test_data['username']
    assert unpacked['age'] == test_data['age']

# Test the CREATE_ACCOUNT_REQUEST message format
# Validates the specific format used for account creation requests
def test_create_account_request_format():
    from shared.message_format import CREATE_ACCOUNT_REQUEST
    
    test_data = {
        'email': 'test@example.com',
        'username': 'testuser',
        'password': 'password123'
    }
    
    packed = CREATE_ACCOUNT_REQUEST.pack(test_data)
    unpacked, _ = CREATE_ACCOUNT_REQUEST.unpack(packed)
    
    assert unpacked == test_data

def test_message_format_pack_errors():
    """Test error cases in MessageFormat.pack()"""
    # Test invalid format character
    format_def = MessageFormat({
        'field': MessageField('field', 's')
    })
    with pytest.raises(ValueError):
        format_def.pack({'field': 123})  # Trying to pack int as string
    
    # Test missing required format
    format_def = MessageFormat({
        'field': MessageField('field')  # No format_char or nested_format
    })
    with pytest.raises(ValueError, match="must have either a format character or be nested"):
        format_def.pack({'field': 'value'})
    
    # Test invalid list value
    format_def = MessageFormat({
        'items': MessageField('items', None, is_nested=True, is_list=True, 
                            nested_format=MessageFormat({'name': MessageField('name', 's')}))
    })
    with pytest.raises(ValueError, match="Expected a list"):
        format_def.pack({'items': 'not a list'})

def test_nested_format_pack_unpack():
    """Test nested format handling"""
    # Define a nested format for user data
    user_format = MessageFormat({
        'name': MessageField('name', 's'),
        'age': MessageField('age', 'i')
    })
    
    # Define a format with nested structure and list
    format_def = MessageFormat({
        'user': MessageField('user', None, is_nested=True, nested_format=user_format),
        'friends': MessageField('friends', None, is_nested=True, is_list=True, nested_format=user_format)
    })
    
    test_data = {
        'user': {
            'name': 'John',
            'age': 30
        },
        'friends': [
            {'name': 'Alice', 'age': 25},
            {'name': 'Bob', 'age': 35}
        ]
    }
    
    # Test packing and unpacking
    packed = format_def.pack(test_data)
    unpacked, _ = format_def.unpack(packed)
    
    # Verify nested structure
    assert unpacked['user']['name'] == test_data['user']['name']
    assert unpacked['user']['age'] == test_data['user']['age']
    
    # Verify nested list
    assert len(unpacked['friends']) == len(test_data['friends'])
    for unpacked_friend, test_friend in zip(unpacked['friends'], test_data['friends']):
        assert unpacked_friend['name'] == test_friend['name']
        assert unpacked_friend['age'] == test_friend['age']

def test_partial_unpack():
    """Test unpacking with incomplete data"""
    format_def = MessageFormat({
        'field1': MessageField('field1', 's'),
        'field2': MessageField('field2', 's')
    })
    
    # Pack only one field
    packed = format_def.pack({'field1': 'value1'})
    unpacked, offset = format_def.unpack(packed)
    
    assert 'field1' in unpacked
    assert unpacked['field1'] == 'value1'
    assert 'field2' not in unpacked

def test_string_list_pack_unpack():
    """Test packing and unpacking lists of strings"""
    format_def = MessageFormat({
        'tags': MessageField('tags', 's', is_list=True)
    })
    
    test_data = {
        'tags': ['python', 'testing', 'networking']
    }
    
    packed = format_def.pack(test_data)
    unpacked, _ = format_def.unpack(packed)
    
    assert unpacked['tags'] == test_data['tags']
    assert len(unpacked['tags']) == 3
    assert unpacked['tags'][0] == 'python'
    assert unpacked['tags'][1] == 'testing'
    assert unpacked['tags'][2] == 'networking'

def test_invalid_string_value():
    """Test error when providing invalid value for string field"""
    format_def = MessageFormat({
        'name': MessageField('name', 's')
    })
    
    # Test with a value that's neither string nor bytes
    with pytest.raises(ValueError, match="expects string or bytes"):
        format_def.pack({'name': 123})  # Integer instead of string

def test_unpack_with_incomplete_data():
    """Test unpacking with data that ends before all fields are processed"""
    format_def = MessageFormat({
        'field1': MessageField('field1', 's'),
        'field2': MessageField('field2', 'i'),
        'field3': MessageField('field3', 's')
    })
    
    # Pack only the first two fields
    test_data = {
        'field1': 'test',
        'field2': 42
    }
    
    packed = format_def.pack(test_data)
    unpacked, offset = format_def.unpack(packed)
    
    # Verify we got what we packed
    assert unpacked['field1'] == 'test'
    assert unpacked['field2'] == 42
    assert 'field3' not in unpacked
    
    first_field_size = 4 + len("test")
    partial_data = packed[:first_field_size]
    
    unpacked_partial, offset_partial = format_def.unpack(partial_data)
    
    assert 'field1' in unpacked_partial
    assert unpacked_partial['field1'] == 'test'
    assert 'field2' not in unpacked_partial

def test_nested_format_errors():
    """Test error cases with nested formats"""
    # Define a nested format
    nested_format = MessageFormat({
        'name': MessageField('name', 's')
    })
    
    # Define a format with a nested field that requires a list
    format_def = MessageFormat({
        'items': MessageField('items', None, is_nested=True, is_list=True, nested_format=nested_format)
    })
    
    # Test with non-list value
    with pytest.raises(ValueError, match="Expected a list"):
        format_def.pack({'items': {'name': 'not a list'}})