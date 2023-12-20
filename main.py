import LoggerConfig
import ConfigManager
import NikeHKRetriever
import NikeHKFectcher
import NikeHKShoe
import asyncio

async def main():
    logger = LoggerConfig.setup_logging()
    config = ConfigManager.load_config()

    s = 'DD1391-100'
    n = NikeHKShoe.NikeHKShoe(s, './')
    await n.update()

if __name__ == '__main__':
    asyncio.run(main())
