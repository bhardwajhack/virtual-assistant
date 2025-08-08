import unittest
from unittest.mock import patch, MagicMock
from .database import PostgresDatabase
from .sql_generator import SQLQueryGenerator

class TestDatabaseIntegration(unittest.TestCase):
    def setUp(self):
        self.db = PostgresDatabase()
        self.sql_generator = SQLQueryGenerator()

    @patch('psycopg2.connect')
    def test_database_connection(self, mock_connect):
        # Mock the database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Test connection
        self.db.connect()
        mock_connect.assert_called_once()
        self.assertIsNotNone(self.db.conn)
        self.assertIsNotNone(self.db.cursor)

    @patch('psycopg2.connect')
    def test_execute_select_query(self, mock_connect):
        # Mock the database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock query results
        expected_results = [
            {'id': 1, 'name': 'Test1'},
            {'id': 2, 'name': 'Test2'}
        ]
        mock_cursor.fetchall.return_value = expected_results

        # Execute test query
        query = "SELECT * FROM test_table"
        results = self.db.execute_query(query)

        # Verify results
        mock_cursor.execute.assert_called_once_with(query, None)
        self.assertEqual(results, expected_results)

    @patch.object(SQLQueryGenerator, 'generate_query')
    @patch.object(PostgresDatabase, 'execute_query')
    def test_sql_generator_with_database(self, mock_execute_query, mock_generate_query):
        # Mock query generation and execution
        test_query = "SELECT * FROM users WHERE age > 25"
        mock_generate_query.return_value = test_query
        
        expected_results = [
            {'id': 1, 'name': 'John', 'age': 30},
            {'id': 2, 'name': 'Jane', 'age': 28}
        ]
        mock_execute_query.return_value = expected_results

        # Test natural language query execution
        results = self.sql_generator.execute_query("Find all users over 25 years old")

        # Verify results
        mock_generate_query.assert_called_once()
        mock_execute_query.assert_called_once_with(test_query, None)
        self.assertEqual(results, expected_results)

if __name__ == '__main__':
    unittest.main()