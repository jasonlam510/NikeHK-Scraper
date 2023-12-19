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
    await NikeHKRetriever.retrieve_loadPdpSizeAndInvList(s)
    n = NikeHKShoe.NikeHKShoe(s, './')
    print(await n.extract_loadSameStyleData(config['dynamic_info']))

if __name__ == '__main__':
    asyncio.run(main())
