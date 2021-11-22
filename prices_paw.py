import redis
import urllib3
import certifi
import socket
import rapidjson as json
import time
import os
import sys
import requests

rdata = redis.StrictRedis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=int(os.getenv('REDIS_DB', '2')))

currency_list = ["ARS", "AUD", "BRL", "BTC", "CAD", "CHF", "CLP", "CNY", "CZK", "DKK", "EUR", "GBP", "HKD", "HUF", "IDR", "ILS", "INR",
                 "JPY", "KRW", "MXN", "MYR", "NOK", "NZD", "PHP", "PKR", "PLN", "RUB", "SEK", "SGD", "THB", "TRY", "TWD", "USD", "ZAR", "SAR", "AED", "KWD", "UAH"]

coingecko_url = 'https://api.coingecko.com/api/v3/coins/banano?localization=false&tickers=true&market_data=true&community_data=false&developer_data=false&sparkline=false'

# monkey patch for ipv6 hang ups
# https://stackoverflow.com/questions/17782142/why-doesnt-requests-get-return-what-is-the-default-timeout-that-requests-get
import socket
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response
            for response in responses
            if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo


def coingecko():
    response = requests.get(url=coingecko_url).json()

    if 'market_data' not in response:
        return
    for currency in currency_list:
        try:
            data_name = currency.lower()
            price_currency = float(0)
            price_currency = float(response['market_data']['current_price'][data_name])
            print(rdata.hset("prices", "coingecko:paw-"+data_name,
                             f"{price_currency:.16f}"), "Coingecko PAW-"+currency, f"{price_currency:.16f}")
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print('exception', exc_type, exc_obj, exc_tb.tb_lineno)
            print("Failed to get price for PAW-"+currency.upper()+" Error")
    ## Convert to VES
    #usdprice = float(rdata.hget(
    #    "prices", "coingecko:paw-usd").decode('utf-8'))
    #bolivarprice = float(rdata.hget(
    #    "prices", "dolartoday:usd-ves").decode('utf-8'))
    #convertedves = usdprice * bolivarprice
    #rdata.hset("prices", "coingecko:paw-ves", f"{convertedves:.16f}")
    #print("Coingecko PAW-VES", rdata.hget("prices",
    #                                         "coingecko:paw-ves").decode('utf-8'))
    # Convert to NANO
    xrb_prices = []
    for t in response['tickers']:
        if t['target'] == 'XRB':
            xrb_prices.append(float(t['last']))
    nanoprice = sum(xrb_prices) / len(xrb_prices)
    rdata.hset("prices", "coingecko:paw-nano", f"{nanoprice:.16f}")
    print(rdata.hset("prices", "coingecko:lastupdate",
                     int(time.time())), int(time.time()))


coingecko()

print("Coingecko PAW-USD:", rdata.hget("prices",
                                          "coingecko:paw-usd").decode('utf-8'))
print("Coingecko PAW-BTC:", rdata.hget("prices",
                                          "coingecko:paw-btc").decode('utf-8'))
print("Coingecko PAW-NANO:", rdata.hget("prices",
                                           "coingecko:paw-nano").decode('utf-8'))
print("Last Update:          ", rdata.hget(
    "prices", "coingecko:lastupdate").decode('utf-8'))
