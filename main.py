import src.LoggerConfig as LoggerConfig
import src.ConfigManager  as ConfigManager
import src.NikeHk.NikeHkwatcher as NikeHkwatcher
import asyncio

async def main():
    logger = LoggerConfig.setup_logging()
    config = ConfigManager.load_config()

    s = 'DD1391-100'
    # n = NikeHKShoe.NikeHKShoe(s, './')
    # await n.update()

if __name__ == '__main__':
    asyncio.run(main())
