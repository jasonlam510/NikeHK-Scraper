import sys,os
sys.path.append(os.getcwd())
import asyncio
import json
from src.LoggerConfig import *
import bs4
import src.nike.NikeHKFectcher as NikeHKFectcher

logger = logging.getLogger(__name__)

async def retrieve_loadSameStyleData(skuCode: str, *args: list) -> (dict, dict):
    """
        Retrieve data for a given SKU code and return a subset of the data based on keys.

        :param skuCode: The skuCode of the shoe to retrieve data for.
        :param keys: A list of keys to extract from the data. If None, returns the full data.
        Range=['abTestCommand', 'activeTime', 'code', 'color', 'firstOnlineTime', 'fob', 'inventory', 'isAbTest', 'isNikeIdSku', 'link', 'listPrice', 'name', 'nameLine1', 'nameLine2', 'nikeIdUrl', 'onShelvesTime', 'rank', 'rankCount', 'sku', 'skuId', 'skuMark', 'skuMark2', 'skuRemark']
        :return: A dictionary containing the extracted data based on keys.
        
        Sample data format:
        {
            'abTestCommand': None,
            'activeTime': 1697524800000,
            'code': 'DD1391-100',
            'color': None,
            'firstOnlineTime': 1609906717018,
            'fob': 749,
            'inventory': 1211,
            'isAbTest': False,
            'isNikeIdSku': None,
            'link': '/product/fair/ks1JNF7G.htm',
            'listPrice': 749,
            'name': '',
            'nameLine1': '',
            'nameLine2': '',
            'nikeIdUrl': None,
            'onShelvesTime': 1697432965344,
            'rank': 74464.7,
            'rankCount': None,
            'sku': None,
            'skuId': None,
            'skuMark': None,
            'skuMark2': None,
            'skuRemark': None
        }
    """    
    full_data = None
    data = await NikeHKFectcher.fetch_loadSameStyleData(skuCode)

    for element in data['colors']:
        if element["code"] == skuCode:
            full_data = element # The skuCode is found
    
    if (full_data is None):
        raise ValueError("SkuCode is not found from the response")
    
    # Extract readable text from skumakr and skuma2k2
    full_data = process_skumark(full_data)

    # Otherwise, extract only the keys of interest
    return tuple({key: full_data.get(key) for key in key_list} for key_list in args)

def process_skumark(full_data: dict) -> dict:
    if ('skuMark' in full_data and full_data['skuMark'] is not None):
        full_data['skuMark'] = json.loads(full_data['skuMark']).get('zh_HK', None) 
    if ('skuMark2' in full_data and full_data['skuMark2']is not None):
        full_data['skuMark2'] = json.loads(full_data['skuMark2']).get('zh_HK', None)
    return full_data


async def retrieve_loadPdpSizeAndInvList(skuCode: str) -> dict[str, list[str]]:
    data = await NikeHKFectcher.fetch_loadPdpSizeAndInvList(skuCode)
    on_stock_size = []
    off_stock_size = []
    for size in data['sizeList']:
        if size["subscribe"] == "t":
            on_stock_size.append(size["size"])
        elif size['subscribe'] == "f":
            off_stock_size.append(size["size"])
    return {"onStockSize" : on_stock_size,\
            "offStockSize" : off_stock_size\
            }
    
async def extract_nikePlpSku(url: str) -> list[str]:
    content = await NikeHKFectcher.fetch_data(url)
    soup = bs4.BeautifulSoup(content, 'html.parser')
    skucodeList = soup.find('input', id='nikePlpSku').get('value')
    return skucodeList.split(',')

async def main():
    logger = setup_logging()
    skucode = 'DD1391-100'
    dynamic_info = ['skuMark', 'skuMark2', 'inventory', 'fob', 'listPrice', 'rank']
    static_info = ['abTestCommand', 'activeTime', 'firstOnlineTime', 'link', 'skuRemark', 'rankCount', 'sku', 'skuId', 'name', 'nameLine1', 'nameLine2', 'nikeIdUrl', 'onShelvesTime', 'isAbTest', 'isNikeIdSku', 'color']
    result = await retrieve_loadSameStyleData(skucode, dynamic_info, static_info)
    print(result)

# Test
if __name__ == '__main__':
    asyncio.run(main())