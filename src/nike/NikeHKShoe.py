import ast
import sys,os
sys.path.append(os.getcwd())
import asyncio
import src.DelayManager as DelayManager
from src.LoggerConfig import *
import src.EmailSender as EmailSender
from src.nike.NikeHKRetriever import *
import pandas as pd
import math
import os
import src.ConfigManager as ConfigManager
from src.nike.NikeHKFectcher import product_url, product_img_url
import aiofiles
from io import StringIO
from time import time

NIKE_URL = "https://www.nike.com.hk"
logger = setup_logging()
logger = logging.getLogger(__name__)

'''
    "Data file name" : [columns fo the data file]

    data
        = all data
        = info + stock
        = dynamic_info + static_info + stoct
'''
SAMPLE_CONFIG = {
    'data_file' : {
        'dynamic_info' : ['skuMark', 'skuMark2', 'inventory', 'fob', 'listPrice', 'rank'],
        'static_info' : ['abTestCommand', 'activeTime', 'firstOnlineTime', 'link', 'skuRemark', 'rankCount', 'sku', 'skuId', 'name', 'nameLine1', 'nameLine2', 'nikeIdUrl', 'onShelvesTime', 'isAbTest', 'isNikeIdSku', 'color'],
        'stock' : ['onStockSize', 'offStockSize']
    },
    'update_csv_timeout' : 5*60,
    'update_csv_max_retry': 2,
    'monitor_shoes' : [{'skucode':'FV0392-100',
                        'monitoring_key' : ['onStockSize']
                        }, 
                        {'skucode':'FB8896-300',
                        'monitoring_key' : ['onStockSize']
                        },
                        {'skucode':'FQ8080-133',
                        'monitoring_key' : ['onStockSize']
                        }
                    ],
    'NikeHKShoe_log_performance' : False
}
config = ConfigManager.load_config(SAMPLE_CONFIG)
DATA_FILE = config['data_file']
UPDATE_CSV_TIMEOUT = config['update_csv_timeout']
UPDATE_CSV_MAX_RETRY = config['update_csv_max_retry']
MONITOR_SHOES = config['monitor_shoes']
P = config['NikeHKShoe_log_performance']

class NikeHKShoe:
    def __init__(self , skucode: str, path: str): 
        self.skucode = skucode
        self.url = None
        self.path = self.create_folder(path)

    def create_folder(self, path):
        path = f'{path}/{self.skucode}'
        os.makedirs(path, exist_ok=True)
        return path
    
    @classmethod
    async def create(cls, skucode, path):
        instance = cls(skucode, path)
        await instance.update()
        return instance
    
    def csv_path(self, file_name):
        return f'{self.path}/{file_name}.csv'
    
    async def update(self):
        # Update each data file
        start_time = time()
        p1 = self.csv_path('dynamic_info')
        p2 = self.csv_path('static_info')
        p3 = self.csv_path('stock')
        fd, fd3, sd1, sd2, sd3 = await asyncio.gather(
            retrieve_loadSameStyleData(self.skucode, DATA_FILE['dynamic_info'], DATA_FILE['static_info']),
            retrieve_loadPdpSizeAndInvList(self.skucode),
            read_last_row_as_dict(p1),
            read_last_row_as_dict(p2),
            read_last_row_as_dict(p3)
        )

        fd1 = fd[0]
        fd2 = fd[1]
        self.url = product_url() + self.extract_link(fd1 | fd2)

        await asyncio.gather(
            self.compare_dict(sd1, fd1, p1),
            self.compare_dict(sd2, fd2, p2),
            self.compare_dict(sd3, fd3, p3)
        )
        end_time = time()
        if P: logger.info(f"{self.path} finished update in {round(end_time-start_time, 3)}s.")
    
    async def compare_dict(self, old, new, path):
        old = self.clean_old_data(old)
        new = self.clean_new_data(new)
        if (old != new):
            await asyncio.gather(
                self.diff_lookup(old, new),
                self.update_csv(old, new, path)
            )
            logger.info(f"{path} updated.")
     
    @staticmethod           
    def clean_old_data(data: dict) -> dict:
        for k, v in data.items():
            if (type(v) != str and math.isnan(v)): # short-circuot lopgic, to replace nan into None
                data[k] = None
            if k in ['onStockSize', 'offStockSize']: # clear list stored as str
                data[k] = ast.literal_eval(v)
            pass
        return data
    
    @staticmethod
    def clean_new_data(data: dict)-> dict:
        for k, v in data.items():
            if v == "":
                data[k] = None
        return data
   
    async def diff_lookup(self, old: dict, new: dict):
        all_keys = set(old.keys()).union(new.keys())
        for key in all_keys:
            val1 = old.get(key, None)
            val2 = new.get(key, None)
            if val1 != val2:
                # logger.info(f"{self.skucode} | {key}: {val1} -> {val2}")
                if self.isMonitoring(self.skucode, key):
                    if (val1 is None): return # Prevent sending email when initialization
                    await EmailSender.async_send_email_with_image(f"{self.skucode} updated on {key}", f"{key}<br>{val1} -><br>{val2}<br>{self.url}", product_img_url(self.skucode))

    @staticmethod
    def isMonitoring(skucode: str, keys: str)-> bool:
        notify = False
        for shoe in MONITOR_SHOES:
            if shoe['skucode'] == skucode:
                for key in shoe['monitoring_key']:
                    if key == keys:
                        notify = True
        return notify

    async def update_csv(self, old: dict, new: dict, path: str):
        new = pd.DataFrame([new])
        if (old == {}):
            updated_df = new
        else:
            updated_df = pd.concat([await read_csv_as_df(path), new] , axis=0)
        retry = 0
        while (retry < UPDATE_CSV_MAX_RETRY):
            try:
                updated_df.to_csv(path, index=False)
                break
            except PermissionError as e:
                logger.error(f"{e}: Please close the csv file! ({retry+1})")
                await DelayManager.sleep()
                retry += 1
    
    @staticmethod
    def extract_link(fetch_data: dict)->str:
        if ('link' in fetch_data.keys()):
            return fetch_data['link']

async def read_csv_as_df(csv_file_path)->pd.DataFrame:
    if not os.path.exists(csv_file_path):
        return None
    async with aiofiles.open(csv_file_path, mode='r') as file:
        content = await file.read()
    
        # Use Pandas to read the CSV content
    return pd.read_csv(StringIO(content), sep=",")
    
async def read_last_row_as_dict(csv_file_path)-> dict:
    if not os.path.exists(csv_file_path):
        return {}
    
    async with aiofiles.open(csv_file_path, mode='r') as file:
        content = await file.read()
    
        # Use Pandas to read the CSV content
    df = pd.read_csv(StringIO(content), sep=",")
    
    if df.empty:
        return {}  

    # Convert the last row to a dictionary
    last_row = df.iloc[-1].to_dict()
    return last_row

# Test
async def main():
    # a = await read_last_row_as_dict("./data/DD1391-100/dynamic_info.csv")
    # print(a)
    s = 'DD1391-100'
    n = await NikeHKShoe.create(s, './data')
    print(n)


    # 'monitor_shoes' : [{'skucode':'FV0392-100',
    #                     'monitoring_key' : ['onStockSize']
    #                     }, 
    #                     {'skucode':'FB8896-300',
    #                     'monitoring_key' : ['onStockSize']
    #                     },
    #                     {'skucode':'FQ8080-133',
    #                     'monitoring_key' : ['onStockSize']
    #                     }
    #                 ]
    # result = NikeHKShoe.isMonitoring('FB8896-300', 'onS=')
    # print(result)

if __name__ == '__main__':
    asyncio.run(main())