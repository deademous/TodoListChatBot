import asyncio
from bot.infrastructure.storage_postgres import StoragePostgres


async def main():
    await StoragePostgres().recreate_database()


if __name__ == "__main__":
    asyncio.run(main())
