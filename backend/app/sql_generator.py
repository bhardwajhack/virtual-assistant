
import boto3
import json
from typing import Any, Dict, List, Optional
from database import PostgresDatabase

class SQLQueryGenerator:
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize the SQL Query Generator with AWS Bedrock client and database connection.

        Args:
            region_name (str): AWS region name where Bedrock is available
        """
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=region_name
        )
        self.model_id = "arn:aws:bedrock:us-east-1:381492244990:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        self.db = PostgresDatabase()


    def generate_query(self, text: str, schema: Optional[str] = None) -> str:
        """
        Generate an SQL query from natural language text.

        Args:
            text (str): Natural language description of the desired query
            schema (Optional[str]): Database schema information to provide context

        Returns:
            str: Generated SQL query
        """
        # Construct the prompt

        schema = """
        Database Schema:
        1. CUSTOMERS Table:
           - customer_id (SERIAL PRIMARY KEY)
           - first_name (VARCHAR(50))
           - last_name (VARCHAR(50))
           - email (VARCHAR(100), UNIQUE)
           - phone (VARCHAR(20))
           - created_at (TIMESTAMP)
        
        2. ORDERS Table:
           - order_id (SERIAL PRIMARY KEY)
           - customer_id (INTEGER, FK -> customers)
           - order_date (TIMESTAMP)
           - total_amount (DECIMAL(10,2))
           - status (VARCHAR(20)) [valid values: pending, processing, completed, cancelled]
           - shipping_address (TEXT)
        
        3. PAYMENTS Table:
           - payment_id (SERIAL PRIMARY KEY)
           - order_id (INTEGER, FK -> orders)
           - payment_date (TIMESTAMP)
           - amount (DECIMAL(10,2))
           - payment_method (VARCHAR(50)) [valid values: credit_card, debit_card, bank_transfer, digital_wallet]
           - status (VARCHAR(20)) [valid values: success, pending, failed]
           - transaction_id (VARCHAR(100), UNIQUE)
    
        """

        prompt = "You are an expert SQL developer with deep knowledge of relational databases and query optimization.\n"

        if schema:
            prompt += f"Here is the database schema:\n{schema}\n\n"

        prompt += (
            f"Write a valid and optimized SQL query that fulfills the following request:\n{text}\n\n"
            "Requirements:\n"
            "1. Use correct table and column names exactly as defined in the schema.\n"
            "2. Ensure proper JOINs and filtering conditions based on the request.\n"
            "3. Optimize for clarity and performance.\n"
            "4. Output only the SQL query—do not include explanations, comments, or extra text."
        )

        # Prepare the request body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.0  # Use low temperature for more deterministic results
        }

        try:
            # Invoke Claude model
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            # Parse and return the response
            response_body = json.loads(response.get('body').read())
            query = response_body['content'][0]['text'].strip()

            print("SQL Query Generated: ", query)
            # Validate the query
            if self.validate_query(query):
                query_result = self.db.execute_query(query)

                prompt = (
                    "You are an SQL Analyst. Your job is to explain SQL query results to the user "
                    "in a clear, friendly, and natural way. Do not repeat or describe the SQL query itself—"
                    "only focus on summarizing the results in plain language that a non-technical user can understand. Do not return any special character in response. Just a single sentence that describes the output.\n\n"
                    f"Here is the SQL Query: {query}\n\n"
                    f"SQL Query Output:\n{query_result}\n"
                )

                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 3000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1
                }

                try:
                    response = self.bedrock.invoke_model(
                        modelId=self.model_id,
                        body=json.dumps(body)
                    )

                    # Parse and return the response
                    response_body = json.loads(response.get('body').read())
                    query_result = response_body['content'][0]['text'].strip()

                    print("Query Output: ", query_result)
                    return query_result

                except Exception as e:
                    raise Exception(f"Error invoking Claude model: {str(e)}")


        except Exception as e:
            raise Exception(f"Error generating SQL query: {str(e)}")

    def validate_query(self, query: str) -> bool:
        """
        Enhanced validation of generated SQL query.

        Args:
            query (str): SQL query to validate

        Returns:
            bool: True if query appears valid, False otherwise

        Raises:
            ValueError: If the query is empty or contains potentially unsafe operations
        """
        if not query or not query.strip():
            raise ValueError("Empty query received from Claude model")

        query = query.strip().upper()

        # Check if query starts with common SQL keywords
        valid_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        query_start = query.split()[0]

        if query_start not in valid_starts:
            raise ValueError(f"Query must start with one of: {', '.join(valid_starts)}")

        # Check for potentially unsafe operations
        unsafe_keywords = ['DROP', 'TRUNCATE', 'ALTER', 'GRANT', 'REVOKE']
        if any(keyword in query for keyword in unsafe_keywords):
            raise ValueError("Query contains potentially unsafe operations")

        # Validate basic SQL structure
        if query_start == 'SELECT' and 'FROM' not in query:
            raise ValueError("SELECT query must contain FROM clause")
        elif query_start == 'INSERT' and 'INTO' not in query:
            raise ValueError("INSERT query must contain INTO clause")
        elif query_start == 'UPDATE' and 'SET' not in query:
            raise ValueError("UPDATE query must contain SET clause")
        elif query_start == 'DELETE' and 'FROM' not in query:
            raise ValueError("DELETE query must contain FROM clause")

        return True