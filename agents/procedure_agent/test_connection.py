import os
from dotenv import load_dotenv
import snowflake.connector

# Load the same .env file
load_dotenv()

print("--- Snowflake Connection Test ---")

# Print the variables to make sure they are loaded correctly
print(f"User: {os.getenv('SNOWFLAKE_USER')}")
print(f"Account: {os.getenv('SNOWFLAKE_ACCOUNT')}")
print(f"Database: {os.getenv('SNOWFLAKE_DATABASE')}")

try:
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )
    print("\n✅ SUCCESS: Connection to Snowflake was successful!")
    conn.close()
    print("✅ SUCCESS: Connection closed.")

except Exception as e:
    print(f"\n❌ FAILED: Could not connect to Snowflake.")
    print(f"Error details: {e}")