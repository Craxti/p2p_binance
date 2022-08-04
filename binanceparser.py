import re
import aiohttp
import json
import asyncio


async def getTopMerchants(tradeType: str, asset: str, fiat: str, rows: int, payType: str, session=None) -> list:
    headers = {
        "Content-Type": "application/json",
        "Cookie": "cid=rujCuvlC"
    }
    data = {
        "page": 1,
        "rows": rows,
        "asset": asset,
        "tradeType": tradeType,
        "fiat": fiat,
        "merchantCheck": "false",
        "payTypes": [payType]
    }
    p2p_url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
    if session:
        async with session.post(p2p_url, json=data) as response:
            resp = json.loads(await response.read())
            availablePrices = []
            if resp['code'] == '000000' and resp['data'] != None:
                for merchant in resp['data']:
                    availablePrices.append(float(merchant['adv']['price']))
            else:
                print("Can't get merchants")
            return availablePrices
    else:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(p2p_url, json=data) as response:
                resp = json.loads(await response.read())
                availablePrices = []
                if resp['code'] == '000000' and resp['data'] != None:
                    for merchant in resp['data']:
                        availablePrices.append(float(merchant['adv']['price']))
                else:
                    print("Can't get merchants")
                return availablePrices


async def getTickerSpread(asset: str, fiat: str, payType: str, session=None):
    tasks = []
    headers = {
        "Content-Type": "application/json",
        "Cookie": "cid=rujCuvlC"
    }
    dictoutput = False
    if session:
        dictoutput = True
        tasks.append(asyncio.create_task(getTopMerchants("buy", asset, fiat, 1, payType, session)))
        tasks.append(asyncio.create_task(getTopMerchants("sell", asset, fiat, 1, payType, session)))
        responses = await asyncio.gather(*tasks)
    else:
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks.append(asyncio.create_task(getTopMerchants("buy", asset, fiat, 1, payType, session)))
            tasks.append(asyncio.create_task(getTopMerchants("sell", asset, fiat, 1, payType, session)))
            responses = await asyncio.gather(*tasks)
    buyprice = responses[0][0]
    sellprice = responses[1][0]
    if dictoutput:
        if sellprice/buyprice >= 1:
            return {asset: str(round((buyprice/sellprice-1)*100, 1))+"%"}
        else:
            return {asset: "+"+str(round((buyprice/sellprice-1)*100, 1))+"%"}
    else:
        if sellprice/buyprice >= 1:
            return str(round((buyprice/sellprice-1)*100, 1))+"%"
        else:
            return "+"+str(round((buyprice/sellprice-1)*100, 1))+"%"


async def getTickersSpreads(assets, fiat, payType):
    tasks = []
    headers = {
        "Content-Type": "application/json",
        "Cookie": "cid=rujCuvlC"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        for asset in assets:
            tasks.append(asyncio.create_task(getTickerSpread(asset, fiat, payType, session)))
        responses = await asyncio.gather(*tasks)
    result = {}
    for response in responses:
        (ticker, percent), = response.items()
        result[ticker] = percent
    return result


async def getTickerPrice(firstAsset: str, secondAsset: str):
    price_url = "https://api.binance.com/api/v3/ticker/price?symbol=" + firstAsset + secondAsset
    async with aiohttp.ClientSession() as session:
        async with session.get(price_url) as response:
            resp = json.loads(await response.read())
            if 'price' in resp:
                return float(resp['price'])
            else:
                print("Can't fetch ticker's price, reason:", resp['msg'])
                return 0

#asyncio.get_event_loop().run_until_complete(getTickerSpread("BTC", "RUB", "Tinkoff"))
