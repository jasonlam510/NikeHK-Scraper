from datetime import datetime
import bs4
import json
import aiohttp
import asyncio
import random
import os
import EmailSender
import csv
# FQ8080-133 green
# DD1391-103 grey
# FV0389-100 special
# DD1391-100 black
# FV0392-100 green af

# save daily log(.csv)
# add email noti if new shoe is on
# add email if spec_watch list have update
WATCHLIST = ['FQ8080-133', 'DD1391-103', 'FV0389-100', 'DD1391-100', 'FV0394-100']
PADDING2 = 15

async def random_sleep(max):
    sleep_time = random.uniform(0.5, max)  # Random sleep between 0.5 and 2.5 seconds
    await asyncio.sleep(sleep_time)

def now() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def product_url(skucode: str = "") -> str:
    return "https://www.nike.com.hk" + skucode

class Shoe:
    def __init__(self , skucode, path): 
        self.skucode = skucode
        self.path = path
        self.link = None
        self.data = None
    
    @classmethod
    async def create(cls, skucode, path):
        instance = cls(skucode, path)
        await instance.update()
        return instance


    async def getInfo(self) -> (str, str, int, float, float, int):
        jquery_url=f"https://www.nike.com.hk/product/loadSameStyleData.json?skuCode={self.skucode}"
        headers = {
            'x-requested-with': 'XMLHttpRequest',
            'referer': product_url()
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(jquery_url, headers=headers) as response:
                data = await response.json()
                for s in data['colors']:
                    if s["code"] == self.skucode:
                        s1 = s2 = None
                        if(self.link == None): self.link = s['link']
                        if (s['skuMark'] is not None): s1 = json.loads(s['skuMark']).get('zh_HK', None) 
                        if (s['skuMark2'] is not None): s2 = json.loads(s['skuMark2']).get('zh_HK', None)
                        return {"skuMark" : s1,\
                                "skuMark2" : s2,\
                                "inventory" : s['inventory'],\
                                "listPrice" : s['listPrice'],\
                                "fob" : s['fob'],\
                                "rank" : s['rank']\
                                }
    
    async def getStock(self) -> (list[str], list[str]):
        jquery_url=f"https://www.nike.com.hk/product/loadPdpSizeAndInvList.json?skuCode={self.skucode}"
        headers = {
            'x-requested-with': 'XMLHttpRequest',
            'referer': product_url()
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(jquery_url, headers=headers) as response:
                data = await response.json()
                on_stock_size = []
                off_stock_size = []
                for size in data['sizeList']:
                    if size["subscribe"] == "t":
                        on_stock_size.append(size["size"])
                    elif size['subscribe'] == "f":
                        off_stock_size.append(size["size"])
        return {"on_stock_size" : on_stock_size,\
                "off_stock_size" : off_stock_size\
                }

    async def update(self):
        info =  await self.getInfo()
        stock = await self.getStock()
        data = info | stock
        if (self.data is None): # First get the data of the shoes
            self.data = data
            print(f"{now()} | {self.skucode.ljust(PADDING2)} | {data} | {product_url(self.link)}")
            self.saveCSV(list(self.data.keys()))
            self.saveCSV(list(self.data.values()))
        else:
            have_updates = False
            for key in self.data:
                if key in data:
                    if self.data[key] != data[key]:
                        print(f"{now()} | {self.skucode.ljust(PADDING2)} | {key}: {self.data[key]} -> {data[key]} | {product_url(self.link)}")
                        if(self.skucode in WATCHLIST):
                            EmailSender.send_email(f'{key} update on {self.skucode}', f"{now()} | {self.skucode.ljust(PADDING2)} | {key}: {self.data[key]} -> {data[key]} | {product_url(self.link)}")
                        self.data[key] = data[key]
                        self.saveCSV(list(self.data.values()))
                        have_updates = True
                        
   
            if (not have_updates): print(".", end="")
        
        
    def saveCSV(self, data: list):
        with open(f'{self.path}/{self.skucode}', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([now()] + data)

class NewShoesWatcher:
    def __init__(self, shoesName: str, url: str):
        self.shoesName = shoesName
        self.url = url
        self.watch_list = {}
        os.makedirs(f'./{self.shoesName}', exist_ok=True)


    async def updateShoesList(self):
        isFirstTime = (len(self.watch_list.keys()) == 0)
        for skucode in await self.getAllSkucodes():
            if skucode not in self.watch_list.keys():
                print(f"{now()} | {self.shoesName.ljust(PADDING2)} | New shoe: {skucode}")
                self.watch_list[skucode] = await Shoe.create(skucode, f'./{self.shoesName}')
                if(not isFirstTime):
                    EmailSender.send_email("New shoes", f"{product_url(self.watch_list[skucode].link)}")
            else:
                print(",", end="")
    
    async def updateAllShoesStock(self):
        for s in self.watch_list.values():
            await s.update()
            await random_sleep(5) 
            
    async def run(self):
        print(f"Start: {self.shoesName}")
        while True:
            await self.updateShoesList()
            await random_sleep(5)
            await self.updateAllShoesStock() 
            await random_sleep(10*60)
                 

    async def getAllSkucodes(self) -> list[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                content = await response.text()
                soup = bs4.BeautifulSoup(content, 'html.parser')
                skucodeList = soup.find('input', id='nikePlpSku').get('value')
                return skucodeList.split(',')

async def main():
    dunklow = "https://www.nike.com.hk/man/nike_dunk/list.htm?k=dunk%20low"
    airforce1 = "https://www.nike.com.hk/man/shoe/airforce1/list.htm"
    dunklowWatcher = NewShoesWatcher("Dunk Low", dunklow)
    airforce1Watcher = NewShoesWatcher("Air Force 1", airforce1)
    await asyncio.gather(dunklowWatcher.run(), airforce1Watcher.run())

if __name__ == "__main__":
    asyncio.run(main())

 