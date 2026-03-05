from src.db.session import engine, Base
from src.db.models import Session, Message, Event, LearnerState

async def init_models():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Uncomment to reset
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_models())
