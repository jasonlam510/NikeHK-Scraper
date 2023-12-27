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
                    ]
}
config = ConfigManager.load_config(SAMPLE_CONFIG)
DATA_FILE = config['data_file']
UPDATE_CSV_TIMEOUT = config['update_csv_timeout']
UPDATE_CSV_MAX_RETRY = config['update_csv_max_retry']
MONITOR_SHOES = config['monitor_shoes']

class NikeHKShoe:
    def __init__(self , skucode: str, path: str): 
        self.skucode = skucode
        self.link = None
        self.path = f'{path}/{skucode}' # path of the data folder
    
    @classmethod
    async def create(cls, skucode, path):
        instance = cls(skucode, path)
        await instance.update()
        return instance
    

    def csv_path(self, file_name):
        return f'{self.path}/{file_name}.csv'
    
    async def update(self):
        # Update each data file
        logger.info(f"Start updating: {self.skucode}")
        fd1, fd2, fd3, sd1, sd2, sd3 = await asyncio.gather(
            retrieve_loadSameStyleData(self.skucode, DATA_FILE['dynamic_info'], DATA_FILE['static_info']),
            retrieve_loadPdpSizeAndInvList(self.skucode),
            read_last_row_as_dict(self.csv_path('dynamic_info')),
            read_last_row_as_dict(self.csv_path('static_info')),
            read_last_row_as_dict(self.csv_path('stock'))
        )

        await asyncio.gather(
            self.compare_dict(fd1, sd1),
            self.compare_dict(fd2, sd2),
            self.compare_dict(fd3, sd3)
        )

        # dynamic_data, static_data = await retrieve_loadSameStyleData(self.skucode, DATA_FILE['dynamic_info'], DATA_FILE['static_info'])

        # # Update the link of the shoe
        # new_link = self.extract_link(dynamic_data | static_data)
        # if new_link is not None:
        #     self.link = new_link

        # for file_name in SAMPLE_CONFIG['data_file'].keys():
        #     # Get the stored data and new data(fetch data)
        #     stored_df = self.retrieve_stored_Data(file_name)
        #     if (file_name == 'dynamic_info'):
        #         fetch_data = dynamic_data
        #     elif (file_name == 'static_info'):
        #         fetch_data = static_data
        #     elif(file_name in ['stock']):
        #         fetch_data = await retrieve_loadPdpSizeAndInvList(self.skucode)
        #     else:
        #         error_msg = "Not implemented data file type!"
        #         logger.error(error_msg)
        #         raise ValueError(error_msg)
                    
        #     # If the fetch data is the first data
        #     if (stored_df.empty == True): # No data in csv
        #         await self.update_csv(self.csv_path(file_name), stored_df, fetch_data)
        #         continue

        #     # Convert the latest date as a dictionary
        #     latest_data = stored_df.tail(1).to_dict(orient='records')[0]
        #     latest_data = self.clean_latest_data(latest_data)
        #     fetch_data = self.clean_null(fetch_data)

        #     # Comparison on latest data and fetch data
        #     if (latest_data != fetch_data):
        #         # notify the update
        #         self.notify_update(latest_data, fetch_data)
        #         # Update the csv
        #         await self.update_csv(self.csv_path(file_name), stored_df, fetch_data)
        logger.info(f"Finished updating: {self.skucode}")
    
    async def compare_dict(self, old, new, file_name):
        old = self.clean_old_data(old)
        new = self.clean_new_data(new)
        if (old != new):
            await asyncio.gather(
                self.diff_lookup(old, new),
                self.update_csv(self.csv_path(file_name), old, new)
            )
     
    @staticmethod           
    def clean_old_data(data: dict) -> dict:
        for k, v in data.items():
            if (type(v) != str and math.isnan(v)): # short-circuot lopgic, to replace nan into None
                data[k] = None
            if k in ['onStockSize', 'offStockSize']: # clear list stored as str
                data[k] = ast.literal_eval(v)
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
                logger.info(f"{self.skucode} | {key}: {val1} -> {val2}") # TODO use notify function instead?
                if self.isMonitoring(self.skucode, key):
                    await EmailSender.async_send_email_with_image(f"{self.skucode} updated on {key}", f"{key}<br>{val1} -><br>{val2}<br>{product_url()+self.link}", product_img_url(self.skucode))
    
    @staticmethod
    def isMonitoring(skucode: str, keys: str)-> bool:
        notify = False
        for shoe in MONITOR_SHOES:
            if shoe['skucode'] == skucode:
                for key in shoe['monitoring_key']:
                    if key == keys:
                        notify = True
        return notify

    async def update_csv(self, path: str, df: pd.DataFrame, new_data: dict):
        fetch_df = pd.DataFrame([new_data])
        updated_df = pd.concat([df, fetch_df] , axis=0)
        retry = 0
        while (retry < UPDATE_CSV_MAX_RETRY):
            try:
                updated_df.to_csv(path, index=False)
                break
            except PermissionError as e:
                logger.error(f"{e}: Please close the csv file! ({retry+1})")
                await DelayManager.sleep()
                retry += 1
    
    def extract_link(self, fetch_data: dict)->str:
        if ('link' in fetch_data.keys()):
            return fetch_data['link']
    
    async def read_last_row_as_dict(self, file_name)-> pd.DataFrame:
        csv_file_path = self.csv_path(file_name)
        if not os.path.exists(csv_file_path):
            return None
        
        async with aiofiles.open(csv_file_path, mode='r') as file:
            content = await file.read()
        
         # Use Pandas to read the CSV content
        df = pd.read_csv(pd.compat.StringIO(content))
        
        if df.empty:
            return None  # or return {}, based on your requirement

        # Convert the last row to a dictionary
        last_row = df.iloc[-1].to_dict()
        return last_row
                           
    # async def retrieve_stored_Data(self, file_name: str) -> pd.DataFrame:
    #     # Check wether the data_type is correct
    #     if (file_name not in SAMPLE_CONFIG['data_file'].keys()):
    #         error_msg = "Incorrect data_type!"
    #         logger.error(error_msg)
    #         raise ValueError(error_msg)
        
    #     # Create the file if not excits.
    #     os.makedirs(f'{self.path}', exist_ok=True)
    #     path = self.csv_path(file_name)
    #     if not os.path.exists(path):
    #         # Save the empty DataFrame to a new CSV file with the column specifed in the config
    #         df = pd.DataFrame(columns=DATA_FILE[file_name])
    #         df.to_csv(path, index=False)
    #         logger.warning(f"{path} is not exists. Created a new CSV file.")
    #     return pd.read_csv(path)

async def read_last_row_as_dict(csv_file_path)-> dict:
    if not os.path.exists(csv_file_path):
        return None
    
    async with aiofiles.open(csv_file_path, mode='r') as file:
        content = await file.read()
    
        # Use Pandas to read the CSV content
    df = pd.read_csv(StringIO(content), sep=",")
    
    if df.empty:
        return None  # or return {}, based on your requirement

    # Convert the last row to a dictionary
    last_row = df.iloc[-1].to_dict()
    return last_row

# Test
async def main():
    a = await read_last_row_as_dict("./data/DD1391-100/dynamic_info.csv")
    print(a)
    # s = 'DD1391-100'
    # n = await NikeHKShoe.create(s, '.\data')
    # print(n)
    # logger.info("Done")


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