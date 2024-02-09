import sys,os
sys.path.append(os.getcwd())
import asyncio
from concurrent.futures import ThreadPoolExecutor
import src.nike.NikeHKRetriever as NikeHKRetriever
from src.nike.NikeHKShoe import NikeHKShoe
import src.DelayManager as DelayManager
import src.ConfigManager as ConfigManager
import src.EmailSender as EmailSender
from src.LoggerConfig import *
from src.nike.NikeHKFectcher import product_url, product_img_url
from time import time

logger = logging.getLogger(__name__)
SAMPLE_CONFIG = {
    'max_delay' : 0,
    'NikeHKwatcher_log_performance' : False
}
config = ConfigManager.load_config(SAMPLE_CONFIG)
MAX_DELAY = config['max_delay']
P = config['NikeHKwatcher_log_performance']


class NikeHkwatcher:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.shoes = {}
        self.path = self.create_folder(name)
        
    @classmethod
    async def create(cls, name, url):
        instance = cls(name, url)
        start_time = time()
        await instance.update_shoes_list()
        end_time = time()
        if P: logger.info(f"{instance.path} finished initizion in {round(end_time-start_time, 3)}s.")
        return instance

    def create_folder(self, name):
        path = f'./data/{name}'
        os.makedirs(path, exist_ok=True)
        return path
    
    async def update_shoes_list(self, notify: bool = False) -> list:
        if P: logger.info(f"Start updating shoes list: {self.name}")
        skucodes = await NikeHKRetriever.extract_nikePlpSku(self.url)
        new_shoes = []  # The new shoe objects

        # Create tasks for all shoes that need to be updated
        tasks = [NikeHKShoe.create(code, self.path) for code in skucodes if code not in self.shoes]

        # Run tasks concurrently and collect results
        for shoe in await asyncio.gather(*tasks):
            if shoe:
                self.shoes[shoe.skucode] = shoe
                new_shoes.append(shoe)
        if notify: await self.notify_new_shoes(new_shoes)       
    
    async def update_shoes(self):
        start_time = time()
        tasks = [self.update_shoe(shoe) for shoe in self.shoes.values()]
        await asyncio.gather(*tasks)
        end_time = time()
        if P: logger.info(f"{self.path} finished update in {round(end_time-start_time, 3)}s.")

    async def update_shoe(self, shoe: NikeHKShoe):
        DelayManager.random_sleep(0, MAX_DELAY)
        await shoe.update()                      

    async def notify_new_shoes(self, new_shoes: list[NikeHKShoe]):
        for shoe in new_shoes:
            logger.info(f"{self.path} | New shoe: {shoe.skucode} | {shoe.url}")
            await EmailSender.async_send_email_with_image(f"New shoe: {shoe.skucode}", shoe.url, product_img_url(shoe.skucode))

async def main():
    logger = setup_logging()
    shoes_name = "Air Force 1"
    url = 'https://www.nike.com.hk/man/shoe/airforce1/list.htm'
    airFource1 = await NikeHkwatcher.create(shoes_name, url)

if __name__ == "__main__":
    asyncio.run(main())


