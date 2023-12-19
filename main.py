import LoggerConfig
import ConfigManager
import NikeHKRetriever
import asyncio


logger = LoggerConfig.setup_logging()

async def main():
    print(await NikeHKRetriever.retrieve_loadPdpSizeAndInvList('DD1391-100'))

if __name__ == '__main__':
    asyncio.run(main())
