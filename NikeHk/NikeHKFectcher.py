import asyncio
import logging
import aiohttp
from typing import Union
from LoggerConfig import *

NIKE_URL = "https://www.nike.com.hk"

logger = logging.getLogger(__name__)

def product_url() -> str:
    return NIKE_URL

def validate_json(data) -> dict:
    if not isinstance(data, dict):
        error_message = f"Fetched data is not JSON:\n{data}"
        logger.error(error_message)
        raise ValueError(error_message)
    return data

async def fetch_data(url: str, headers: dict[str:str] = None) -> Union[dict, str]:
    while True:  # Infinite loop to keep trying
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        # Log incorrect response code
                        logger.warning(f"Incorrect response code: {response.status}")
                        continue  # Try again
                    response_type = response.content_type
                    if response_type == 'application/json':
                        return await response.json()
                    elif response_type == 'text/html':
                        return await response.text()
                    else:
                        # Handle other content types or raise an exception
                        logger.warning(f"Unhandled response content type: {response_type}\n{response.read()}")       
        except aiohttp.ClientError as e:
            # Log client errors (like no network connection)
            logger.error(f"Client error: {e}")
        except asyncio.TimeoutError:
            # Log timeout errors
            logger.error("Request timed out")
        except Exception as e:
            # Log other potential exceptions
            logger.exception(f"{e}")
            break  # Break the loop if an unrecoverable error occurs

        await asyncio.sleep(1)  # Wait a bit before trying again

async def fetch_loadSameStyleData(skuCode: str) -> Union[dict, str]:
    jquery_url=f"https://www.nike.com.hk/product/loadSameStyleData.json?skuCode={skuCode}"
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'referer': product_url()
    }

    data = await fetch_data(jquery_url, headers)
    return validate_json(data)
    
async def fetch_loadPdpSizeAndInvList(skuCode: str):
    jquery_url=f"https://www.nike.com.hk/product/loadPdpSizeAndInvList.json?skuCode={skuCode}"
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'referer': product_url()
    }
    data = await fetch_data(jquery_url, headers)
    return data

# Test
if __name__ == '__main__':
    logger = setup_logging()