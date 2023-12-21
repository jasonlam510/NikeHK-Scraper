import LoggerConfig
import ConfigManager
import NikeHK.NikeHKRetriever as NikeHKRetriever
import NikeHK.NikeHKFectcher as  NikeHKFectcher
import NikeHK.NikeHKShoe as NikeHKShoe
import asyncio

async def main():
    logger = LoggerConfig.setup_logging()
    config = ConfigManager.load_config()

    s = 'DD1391-100'
    n = NikeHKShoe.NikeHKShoe(s, './')
    await n.update()

if __name__ == '__main__':
    asyncio.run(main())
