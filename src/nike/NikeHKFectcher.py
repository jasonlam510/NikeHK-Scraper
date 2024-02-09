import sys,os
import src.ConfigManager as ConfigManager
sys.path.append(os.getcwd())
import src.LoggerConfig as LoggerConfig
import asyncio
import logging
import aiohttp
from typing import Union

logger = logging.getLogger(__name__)

SAMPLE_CONFIG = {
    'max_fetch_data_retry' : 5,
    'fetch_data_retry_delay' : 5,
    'nike_url' : 'https://www.nike.com.hk'
}
config = ConfigManager.load_config(SAMPLE_CONFIG)
MAX_FETCH_DATA_RETRY = config['max_delay']
FETCH_DATA_RETRY_DELAY = config['fetch_data_retry_delay']   
NIKE_URL = config['nike_url']

def product_url() -> str:
    return NIKE_URL

def product_img_url(skucode: str) -> str:
    return f'https://static.nike.com.hk/resources/product/{skucode}/{skucode}_BL1.png'

def validate_json(data, error_message) -> dict:
    if not isinstance(data, dict):
        raise TypeError(f"Fetched data from {error_message} is {type(data)} not JSON:\n{data}")
    if (data is None):
        raise ValueError(f"No data fetched from {error_message}")
    return data

# Retry only when the response code is not 200, client error and timeout error.
async def fetch_data(url: str, headers: dict[str:str] = None) -> Union[dict, str]:
    retry = 0
    while retry < MAX_FETCH_DATA_RETRY:  
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        # Log incorrect response code
                        logger.warning(f"[{retry+1}]Incorrect response code while fetching {url}\n{response.status} ")
                        continue  # Try again

                    response_type = response.content_type
                    if response_type == 'application/json':
                        return await response.json()
                    elif response_type == 'text/html':
                        return await response.text()
                    else:
                        # Handle other content types or raise an exception
                        raise TypeError(f"[{retry+1}]Unhandled response content type({response_type}) while fetching {url}:\n{response.read()}")       
        except aiohttp.ClientError as e:
            # Log client errors (like no network connection)
            logger.warning(f"[{retry+1}]Client error while fetching {url}: {e}")
        except asyncio.TimeoutError:
            # Log timeout errors
            logger.warning(f"[{retry+1}]Request timed out while fetching {url}")
        except Exception as e:
            # Log other potential exceptions
            logger.exception(f"{e}")
            raise e

        retry += 1
        await asyncio.sleep(FETCH_DATA_RETRY_DELAY)  # Wait a bit before trying again

async def fetch_loadSameStyleData(skuCode: str) -> Union[dict, str]:
    jquery_url=f"https://www.nike.com.hk/product/loadSameStyleData.json?skuCode={skuCode}"
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'referer': product_url()
    }

    data = await fetch_data(jquery_url, headers)
    try:
        return validate_json(data, skuCode)
    except Exception as e:
        logger.exception(f"{e}")
        raise e
    
async def fetch_loadPdpSizeAndInvList(skuCode: str):
    jquery_url=f"https://www.nike.com.hk/product/loadPdpSizeAndInvList.json?skuCode={skuCode}"
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'referer': product_url()
    }
    data = await fetch_data(jquery_url, headers)
    try:
        return validate_json(data, skuCode)
    except Exception as e:
        logger.exception(f"{e}")
        raise e

# Test
if __name__ == '__main__':
    logger = LoggerConfig.setup_logging()