# services/conversion/db.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from typing import Optional
from config import settings

mongo_client: Optional[AsyncIOMotorClient] = None
db = None
gridfs_bucket: Optional[AsyncIOMotorGridFSBucket] = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global mongo_client, db, gridfs_bucket
    mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    db = mongo_client[settings.MONGO_DB]
    gridfs_bucket = AsyncIOMotorGridFSBucket(db)


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()


def get_db():
    """Get database instance"""
    return db


def get_gridfs_bucket():
    """Get GridFS bucket instance"""
    return gridfs_bucket
