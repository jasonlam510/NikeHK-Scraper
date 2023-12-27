import sys,os
sys.path.append(os.getcwd())
import src.LoggerConfig as LoggerConfig
logger = LoggerConfig.setup_logging()
import src.ConfigManager  as ConfigManager
from src.nike.NikeHkwatcher import NikeHkwatcher
import src.DelayManager as DelayManager
import asyncio

SAMPLE_CONFIG = {
    'scrap_list' : [{'name' : 'Dunk low',
                     'url' : 'https://www.nike.com.hk/man/nike_dunk/list.htm?k=dunk%20low'
                     },
                    
                    ]
}
# {'name' : 'Airforce1',
#                      'url' : 'https://www.nike.com.hk/man/shoe/airforce1/list.htm'
#                      }
config = ConfigManager.load_config(SAMPLE_CONFIG)
SCRAP_LIST = config['scrap_list' ]

async def main():
    logger = LoggerConfig.setup_logging()
    config = ConfigManager.load_config()

    watchers = [await NikeHkwatcher.create(ele['name'], ele['url']) for ele in SCRAP_LIST]
    while (True):
        logger.info("Start sleeping")
        DelayManager.sleep(30)
        for watcher in watchers:
            await watcher.update_shoes_list()
            await watcher.update_shoes()


if __name__ == '__main__':
    asyncio.run(main())
