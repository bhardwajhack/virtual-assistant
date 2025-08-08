import unittest
from unittest.mock import patch, MagicMock
from sql_generator import SQLQueryGenerator
import json
from io import BytesIO

class TestSQLQueryGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = SQLQueryGenerator()

    @patch('boto3.client')
    def test_generate_query_basic(self, mock_boto3_client):
        # Mock response from Bedrock
        mock_response = {
            'body': BytesIO(json.dumps({
                'content': [{'text': 'SELECT * FROM users WHERE age > 25;'}]
            }).encode())
        }
        
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = mock_response
        mock_boto3_client.return_value = mock_client

        # Test query generation
        query = self.generator.generate_query("Get all users over 25 years old")
        self.assertEqual(query, 'SELECT * FROM users WHERE age > 25;')

    @patch('boto3.client')
    def test_generate_query_with_schema(self, mock_boto3_client):
        # Mock response
        mock_response = {
            'body': BytesIO(json.dumps({
                'content': [{'text': 'SELECT name, email FROM customers WHERE status = "active";'}]
            }).encode())
        }
        
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = mock_response
        mock_boto3_client.return_value = mock_client

        schema = """
        CREATE TABLE customers (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255),
            status VARCHAR(20)
        );
        """
        
        query = self.generator.generate_query(
            "List names and emails of active customers",
            schema=schema
        )
        self.assertEqual(query, 'SELECT name, email FROM customers WHERE status = "active";')

    def test_validate_query(self):
        # Test valid queries
        self.assertTrue(self.generator.validate_query("SELECT * FROM users;"))
        self.assertTrue(self.generator.validate_query("INSERT INTO users (name) VALUES ('John');"))
        self.assertTrue(self.generator.validate_query("UPDATE users SET name = 'John';"))
        self.assertTrue(self.generator.validate_query("DELETE FROM users WHERE id = 1;"))
        
        # Test invalid queries
        self.assertFalse(self.generator.validate_query("INVALID QUERY"))
        self.assertFalse(self.generator.validate_query(""))
        self.assertFalse(self.generator.validate_query("users SELECT * FROM"))

if __name__ == '__main__':
    unittest.main()