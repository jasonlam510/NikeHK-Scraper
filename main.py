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
                    {'name' : 'Airforce1',
                     'url' : 'https://www.nike.com.hk/man/shoe/airforce1/list.htm'
                    }
                ],
    'update_delay' : 30,
    'watcher_delay' : 15
}
config = ConfigManager.load_config(SAMPLE_CONFIG)
SCRAP_LIST = config['scrap_list']
UPDATE_DELAY = config['update_delay']
WATCHER_DELAY = config['watcher_delay']

async def main():
    logger = LoggerConfig.setup_logging()
    watchers = []

    # watchers = [await NikeHkwatcher.create(ele['name'], ele['url']) for ele in SCRAP_LIST]
    for ele in SCRAP_LIST:
        watcher = await NikeHkwatcher.create(ele['name'], ele['url'])
        watchers.append(watcher)
        logger.info(f"Start watcher_delay: {WATCHER_DELAY}s")
        DelayManager.sleep(WATCHER_DELAY)

    while (True):
        logger.info(f"Start update_delay: {UPDATE_DELAY}*60 s")
        DelayManager.sleep(UPDATE_DELAY*60)
        for watcher in watchers:
            await watcher.update()
            logger.info(f"Start watcher_delay: {WATCHER_DELAY}s")
            DelayManager.sleep(WATCHER_DELAY)
            
if __name__ == '__main__':
    asyncio.run(main())
