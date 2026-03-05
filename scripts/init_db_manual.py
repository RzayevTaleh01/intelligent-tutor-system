from src.db.init_db import init_models
import asyncio

if __name__ == "__main__":
    asyncio.run(init_models())
