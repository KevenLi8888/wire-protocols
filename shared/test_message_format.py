import unittest
from shared.message_format import MessageFormat, MessageField

class TestMessageFormat(unittest.TestCase):
    def setUp(self):
        # Basic format with primitive types
        self.basic_format = MessageFormat({
            'string_field': MessageField('string_field', 's'),
            'int_field': MessageField('int_field', 'i'),
        })

        # Nested format
        self.user_format = MessageFormat({
            'id': MessageField('id', 's'),
            'name': MessageField('name', 's'),
        })
        
        self.nested_format = MessageFormat({
            'code': MessageField('code', 'i'),
            'user': MessageField('user', None, is_nested=True, nested_format=self.user_format)
        })

        # List format
        self.list_format = MessageFormat({
            'count': MessageField('count', 'i'),
            'items': MessageField('items', 's', is_list=True)
        })

        # Nested list format
        self.nested_list_format = MessageFormat({
            'count': MessageField('count', 'i'),
            'users': MessageField('users', None, is_nested=True, is_list=True, nested_format=self.user_format)
        })

    def test_basic_pack_unpack(self):
        data = {
            'string_field': 'test',
            'int_field': 42
        }
        packed = self.basic_format.pack(data)
        unpacked = self.basic_format.unpack(packed)
        self.assertEqual(data, unpacked)

    def test_nested_pack_unpack(self):
        data = {
            'code': 200,
            'user': {
                'id': '123',
                'name': 'John'
            }
        }
        packed = self.nested_format.pack(data)
        unpacked = self.nested_format.unpack(packed)
        self.assertEqual(data, unpacked)

    def test_list_pack_unpack(self):
        data = {
            'count': 3,
            'items': ['one', 'two', 'three']
        }
        packed = self.list_format.pack(data)
        unpacked = self.list_format.unpack(packed)
        self.assertEqual(data, unpacked)

    def test_nested_list_pack_unpack(self):
        data = {
            'count': 2,
            'users': [
                {'id': '1', 'name': 'John'},
                {'id': '2', 'name': 'Jane'}
            ]
        }
        packed = self.nested_list_format.pack(data)
        unpacked = self.nested_list_format.unpack(packed)
        self.assertEqual(data, unpacked)

    def test_escape_characters(self):
        format = MessageFormat({
            'text': MessageField('text', 's')
        })
        
        test_cases = [
            'test\\with\\backslashes',
            'test\0with\0nulls',
            'test\1with\1list\1delimiters',
            'mixed\\test\0with\1all\\delimiters',
            '\\\\double\\\\backslashes'
        ]
        
        for test_str in test_cases:
            data = {'text': test_str}
            packed = format.pack(data)
            unpacked = format.unpack(packed)
            self.assertEqual(data, unpacked, f"Failed to preserve string: {test_str}")

    def test_empty_values(self):
        data = {
            'string_field': '',
            'int_field': 0
        }
        packed = self.basic_format.pack(data)
        unpacked = self.basic_format.unpack(packed)
        self.assertEqual(data, unpacked)

if __name__ == '__main__':
    unittest.main()
