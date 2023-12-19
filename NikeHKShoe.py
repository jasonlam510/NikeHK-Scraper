import json
import NikeHKRetriever
import logging
import pandas as pd
import os
import ConfigManager

logger = logging.getLogger(__name__)

'''
    "Data file name" : [columns fo the data file]

    data
        = all data
        = info + stock
        = dynamic_info + static_info + stoct
'''
SAMPLE_CONFIG = {
    'dynamic_info' : ['skuMark', 'skuMark2', 'inventory', 'fob', 'listPrice', 'rank', 'inventory', ],
    'static_info' : ['abTestCommand', 'activeTime', 'firstOnlineTime', 'link', 'skuRemark', 'rankCount', 'sku', 'skuId', 'name', 'nameLine1', 'nameLine2', 'nikeIdUrl', 'onShelvesTime', 'isAbTest', 'isNikeIdSku', 'color'],
    'stock' : ['onStockSize', 'offStockSize']
}
config = ConfigManager.load_config(SAMPLE_CONFIG)

NIKE_URL = "https://www.nike.com.hk"

class NikeHKShoe:
    def __init__(self , skucode: str, path: str): 
        self.skucode = skucode
        self.path = f'{path}/{skucode}' # path of the data folder
    
    @classmethod
    async def create(cls, skucode, path):
        instance = cls(skucode, path)
        await instance.update()
        return instance
    
    async def update(self):
        for datafile in config.keys():
            stored_data = self.retrieve_data_by_type(datafile)
            if(datafile in ['dynamic_info', 'static_info']):
                fetch_Dataframe = NikeHKRetriever.retrieve_loadSameStyleData(self.skucode, datafile)
            elif(datafile in ['stock']):
                fetch_Dataframe = NikeHKRetriever.retrieve_loadPdpSizeAndInvList(self.skucode)
            else:
                error_msg = "Not implemented data file type!"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
        # TODO Implement the comparison
    
    async def retrieve_stored_Data_by_type(self, data_type: str) -> dict:
        # Check wether the data_type is correct
        if (data_type not in SAMPLE_CONFIG.keys()):
            error_msg = "Incorrect data_type!"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create the file if not excits.
        os.makedirs(f'{self.path}', exist_ok=True)
        csv_path = f'{self.path}/{data_type}.csv'
        if not os.path.exists(csv_path):
            # Save the DataFrame to a new CSV file with the column specifed in the config
            df = pd.DataFrame(columns=config[data_type])
            df.to_csv(csv_path, index=False)
            logger.warning(f"{csv_path} is not exists. Created a new CSV file.")
            return None
        
        # Rertrieve the last row of the .csv
        return pd.read_csv('csv_path').iloc[-1].to_dict()

    async def extract_loadSameStyleData(self) -> dict[str:str]:
        data = NikeHKRetriever.retrieve_loadSameStyleData(self.skucode, ['skuMark', 'skuMark2', 'inventory', 'fob', 'listPrice', 'rank', 'inventory', 'firstOnlineTime', 'link'])
        if (data['skuMark'] is not None):
            data['skuMark'] = json.loads(data['skuMark']).get('zh_HK', None) 
        if (data['skuMark2'] is not None):
            data['skuMark2'] = json.loads(data['skuMark']).get('zh_HK', None) 
        return data

