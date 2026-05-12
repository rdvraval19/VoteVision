# app/database.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Grab the database URL we added to .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the async engine — this is the actual connection pool to PostgreSQL
# echo=True logs every SQL query to the console (great for debugging, turn off in production)
engine = create_async_engine(DATABASE_URL, echo=True)

# Session factory — creates new AsyncSession objects for each request
# expire_on_commit=False means objects stay usable after a commit
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class that all SQLAlchemy DB models will inherit from
class Base(DeclarativeBase):
    pass

# Dependency function — FastAPI will call this automatically for routes that need DB access
# It yields a session, then closes it when the request is done (even if an error occurs)
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session          # hand the session to the route
            await session.commit() # save changes if no error
        except Exception:
            await session.rollback() # undo changes if something went wrong
            raise                    # re-raise the error so FastAPI handles it