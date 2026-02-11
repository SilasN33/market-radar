import unittest
from unittest.mock import MagicMock
from src.database.patch import PostgreSQLCursor, PostgreSQLAdapter

class TestPostgresPatch(unittest.TestCase):
    def test_sql_translation_datetime(self):
        # Setup
        mock_cursor = MagicMock()
        pg_cursor = PostgreSQLCursor(mock_cursor)
        
        # Action: Execute command that failed in CI
        sql = "ALTER TABLE opportunities ADD COLUMN last_updated DATETIME"
        pg_cursor.execute(sql)
        
        # Assert: Check if DATETIME was replaced by TIMESTAMP
        # The mock_cursor.execute receives the translated SQL as first argument
        args, _ = mock_cursor.execute.call_args
        translated_sql = args[0]
        
        self.assertIn("TIMESTAMP", translated_sql, "DATETIME should be replaced by TIMESTAMP")
        self.assertNotIn("DATETIME", translated_sql, "DATETIME should be removed")
        print(f"✅ Translated SQL: {translated_sql}")

    def test_adapter_rollback(self):
        # Setup
        mock_conn = MagicMock()
        adapter = PostgreSQLAdapter(mock_conn)
        
        # Action
        try:
            adapter.rollback()
        except AttributeError:
            self.fail("PostgreSQLAdapter has no rollback method!")
            
        # Assert
        mock_conn.rollback.assert_called_once()
        print("✅ Adapter.rollback() called successfully")

if __name__ == '__main__':
    unittest.main()
