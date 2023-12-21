import asyncio
import DelayManager
import NikeHKRetriever
import logging
import pandas as pd
import math
import os
import ConfigManager

NIKE_URL = "https://www.nike.com.hk"

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
    'update_csv_max_retry': 2
}
config = ConfigManager.load_config(SAMPLE_CONFIG)

class NikeHKShoe:
    def __init__(self , skucode: str, path: str): 
        self.skucode = skucode
        self.path = f'{path}/{skucode}' # path of the data folder
    
    @classmethod
    async def create(cls, skucode, path):
        instance = cls(skucode, path)
        await instance.update()
        return instance
    
    def csv_path(self, datafile):
        return f'{self.path}/{datafile}.csv'
    
    def retrieve_datafile_config(self, filename: str = None) -> list:
        if filename == None:
            return config['data_file']
        return config['data_file'][filename]
    
    async def update(self):
        # Update each data file
        for file_name in SAMPLE_CONFIG['data_file'].keys():
            # Get the stored data and new data(fetch data)
            stored_df = self.retrieve_stored_Data(file_name)
            if(file_name in ['dynamic_info', 'static_info']):
                fetch_data = await NikeHKRetriever.retrieve_loadSameStyleData(self.skucode, self.retrieve_datafile_config(file_name))
            elif(file_name in ['stock']):
                fetch_data = await NikeHKRetriever.retrieve_loadPdpSizeAndInvList(self.skucode)
            else:
                error_msg = "Not implemented data file type!"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # If the fetch data is the first data
            if (stored_df.empty == True): # No data in csv
                await self.update_csv(self.csv_path(file_name), stored_df, fetch_data)
                continue

            # Convert the latest date as a dictionary
            latest_data = stored_df.tail(1).to_dict(orient='records')[0]
            latest_data = self.clean_nan(latest_data)

            # Comparison on latest data and fetch data
            if (latest_data != fetch_data):
                # notify the update
                self.notify_update(latest_data, fetch_data)
                # Update the csv
                await self.update_csv(self.csv_path(file_name), stored_df, fetch_data)
                
    def clean_nan(self, dict: dict) -> dict:
        for k, v in dict.items():
            if (type(v) != str and math.isnan(v)): # short-circuot lopgic, to replace nan into None
                dict[k] = None
        return dict
    
    def notify_update(self, latest_data: dict, fetch_data: dict):
        all_keys = set(latest_data.keys()).union(fetch_data.keys())
        for key in all_keys:
            val1 = latest_data.get(key, None)
            val2 = fetch_data.get(key, None)
            if val1 != val2:
                logger.info(f"{self.skucode} | {key}: {val1} -> {val2}") # TODO use notify function instead?
    
    async def update_csv(self, path: str, df: pd.DataFrame, new_data: dict):
        fetch_df = pd.DataFrame([new_data])
        updated_df = pd.concat([df, fetch_df] , axis=0)
        retry = 0
        while (retry < config['update_csv_max_retry']):
            try:
                updated_df.to_csv(path)
                break
            except PermissionError as e:
                logger.error(f"{e}: Please close the csv file! ({retry+1})")
                await DelayManager.sleep(config['update_csv_timeout'])
                retry += 1
                       
    def retrieve_stored_Data(self, datafile: str) -> pd.DataFrame:
        # Check wether the data_type is correct
        if (datafile not in SAMPLE_CONFIG['data_file'].keys()):
            error_msg = "Incorrect data_type!"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create the file if not excits.
        os.makedirs(f'{self.path}', exist_ok=True)
        path = self.csv_path(datafile)
        if not os.path.exists(path):
            # Save the empty DataFrame to a new CSV file with the column specifed in the config
            df = pd.DataFrame(columns=self.retrieve_datafile_config(datafile))
            df.to_csv(path)
            logger.warning(f"{path} is not exists. Created a new CSV file.")
        return pd.read_csv(path)

# Test
async def main():
    s = 'DD1391-100'
    n = NikeHKShoe(s, '.')
    await n.update()

if __name__ == '__main__':
    asyncio.run(main())