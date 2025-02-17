import os

if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv

    load_dotenv()