import os
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

class PostgresDatabase:
    def __init__(self):
        """Initialize PostgreSQL database connection."""
        self.connection_params = {
            'dbname': 'aws_sample_db',
            'user': 'postgres',
            'password': 'postgres',
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432')
        }
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """Establish connection to the PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        except Exception as e:
            raise Exception(f"Error connecting to PostgreSQL database: {str(e)}")

    def disconnect(self) -> None:
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return the results.

        Args:
            query (str): SQL query to execute
            params (Optional[Dict[str, Any]]): Query parameters for parameterized queries

        Returns:
            List[Dict[str, Any]]: Query results as a list of dictionaries
        """
        try:
            if not self.conn or self.conn.closed:
                self.connect()

            self.cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                results = self.cursor.fetchall()
                return [dict(row) for row in results]
            else:
                self.conn.commit()
                return []

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error executing query: {str(e)}")

    def get_schema(self) -> str:
        """
        Get the database schema information.

        Returns:
            str: Database schema information
        """
        try:
            if not self.conn or self.conn.closed:
                self.connect()

            # Query to get table and column information
            schema_query = """
                SELECT 
                    t.table_name,
                    array_agg(
                        c.column_name || ' ' || c.data_type || 
                        CASE 
                            WHEN c.character_maximum_length IS NOT NULL 
                            THEN '(' || c.character_maximum_length || ')'
                            ELSE ''
                        END
                    ) as columns
                FROM 
                    information_schema.tables t
                    JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE 
                    t.table_schema = 'public'
                GROUP BY 
                    t.table_name;
            """

            self.cursor.execute(schema_query)
            results = self.cursor.fetchall()

            schema_str = "Database Schema:\n"
            for row in results:
                schema_str += f"\nTable: {row['table_name']}\n"
                schema_str += "Columns:\n"
                for column in row['columns']:
                    schema_str += f"  - {column}\n"

            return schema_str

        except Exception as e:
            raise Exception(f"Error fetching schema: {str(e)}")