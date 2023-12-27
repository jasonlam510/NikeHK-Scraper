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

logger = logging.getLogger(__name__)
SAMPLE_CONFIG = {
    'max_delay' : 0.5,
    'max_workers' : 16
}
config = ConfigManager.load_config(SAMPLE_CONFIG)
MAX_DELAY = config['max_delay']
MAX_WORKERS = config['max_workers']

class NikeHkwatcher:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.shoes = {}
        self.path = self.create_folder(name)
        
    @classmethod
    async def create(cls, name, url):
        instance = cls(name, url)
        await instance.update_shoes_list()
        return instance

    def create_folder(self, name):
        path = f'./data/{name}'
        os.makedirs(path, exist_ok=True)
        return path

    async def update_shoes_list(self) -> list:
        logger.info(f"Start updating shoes list: {self.name}")
        skucodes = await NikeHKRetriever.extract_nikePlpSku(self.url)
        new_shoes = []  # The new shoe objects

        def create_shoe(code):
            return asyncio.run(NikeHKShoe.create(code, self.path))

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(create_shoe, code) for code in skucodes if code not in self.shoes]
            for future in futures:
                shoe = future.result()
                if shoe:
                    self.shoes[shoe.skucode] = shoe 
                    new_shoes.append(shoe)

        logger.info(f"Finished updating shoes list: {self.name}")
        return new_shoes
    
    async def update_shoes(self):

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for shoe in self.shoes.values():
                executor.submit(self.update_shoe, shoe)

    async def update_shoe(self, shoe: NikeHKShoe):
        # Random delay before updating
        # DelayManager.random_sleep(0, MAX_DELAY)
        logger.info(f"Start calling: {shoe.skucode} to update")
        await shoe.update()
    
    async def update(self):
        new_shoes = await self.update_shoes_list()
        self.notify_new_shoes(new_shoes)
        self.update_shoes()

    def notify_new_shoes(self, new_shoes: list[NikeHKShoe]):
        for shoe in new_shoes:
            EmailSender.send_email_with_image(f"New shoe: {shoe.skucode}", product_url()+shoe.url, product_img_url(shoe.skucode))

async def main():
    logger = setup_logging()
    shoes_name = "Air Force 1"
    url = 'https://www.nike.com.hk/man/shoe/airforce1/list.htm'
    airFource1 = await NikeHkwatcher.create(shoes_name, url)

if __name__ == "__main__":
    asyncio.run(main())


