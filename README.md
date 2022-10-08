# Official Python SDK for Alice Blue API

The Official Python library for communicating with the Alice Blue APIs.

Alice Blue Python library provides an easy to use wrapper over the HTTPS APIs.

The HTTP calls have been converted to methods and JSON responses are wrapped into Python-compatible objects.

Websocket connections are handled automatically within the library.

* __Author: [krishnavelu](https://github.com/krishnavelu/)__
* [Unofficed](https://www.unofficed.com/) is strategic partner of Alice Blue responsible for this git.
* Alice Blue API trading is free for [Unofficed](https://www.unofficed.com/) members. Follow [this](https://unofficed.com/alice-blue/) to get API free.

## Installation

This module is installed via pip:

```
pip install alice_blue
```

To force upgrade existing installations:
```
pip uninstall alice_blue
pip --no-cache-dir install --upgrade alice_blue
```

## Getting started with API

### Overview
There is only one class in the whole library: `AliceBlue`. The `login_and_get_sessionID()` static method is used to retrieve session ID from alice blue server. A session ID is valid for 24 hours.
With session ID, you can instantiate an AliceBlue object. Ideally you only need to create a session ID once every day. Once the session ID is created new, it'll be stored in a temporary location. Next time, the same session ID will be used.

### REST Documentation
The original REST API documentation is available [here](https://v2api.aliceblueonline.com/).

## Using the API

### Logging
The whole library is equipped with python's `logging` module for debugging. If more debug information is needed, enable logging using the following code.

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Geting API Id and API secret
api_secret is unique for each and every account. You need to enable api trading and get api_secret from alice blue.
1. Login to [developer console](http://developers.aliceblueonline.com).
1. Click on 'Create New App'.
1. Enter 'App Name' as you like. Enter 'Redirect URL' and 'Post Back URL' as `https://ant.aliceblueonline.com/plugin/callback`.
1. Click on 'Save'.
1. Copy the 'App Code' and 'App Secret'. You will need these to generate a session ID.

### Getting an session ID
1. Import alice_blue
```python
from alice_blue import *
```

2. Create `session_id` using `login_and_get_sessionID()` function  with your `username`, `password`, `2FA (2fa is now year of birth)`, `app_id` and `api_secret`.
```python
session_id = AliceBlue.login_and_get_sessionID(   username    = "username", 
                                                    password    = "password", 
                                                    twoFA       = "1993",
                                                    app_id      = "app_id",
                                                    api_secret  = "api_secret")
```

### Problem getting access token
If you are facing problem getting access token, make sure the following are correct.
1. username.
1. password.
1. 2FA.
1. api secret.
1. app id.

Even after verifying all these, if you are facing problem, contact alice customer care. They should enable the API access in their end. Don't create a new issue in this library for OAuth Error.

### Create AliceBlue Object
Once you have your `session_id`, you can create an AliceBlue object with your `session_id` and `username`.
```python
alice = AliceBlue(username = "username", session_id = session_id)
```

You can run these commands to check your newly created alice blue object.
1. [Get Balance](#get-balance)
1. [Get Profile](#get-profile)
1. [Get Daywise positions](#get-daywise-positions)
1. [Get Netwise positions](#get-netwise-positions)
1. [Get Holding positions](#get-holding-positions)

### Get Balance
Code:
```python
print(alice.get_balance()) # get balance / margin limits
```
Sample response
```
[{'symbol': 'ALL', 'cncMarginUsed': '0', 'spanmargin': '159440.00', 'branchAdhoc': '0.000000', 'adhocMargin': '0.000000', 'payoutamount': '0.00', 'cdsSpreadBenefit': '0', 'adhocscripmargin': '0.00', 'exposuremargin': '7774.30', 'scripbasketmargin': '0.00', 'credits': '114028.29', 'segment': 'ALL', 'net': '95012.20', 'turnover': '0.00', 'grossexposurevalue': '0.00', 'mfssAmountUsed': '0.00', 'realizedMtomPrsnt': '-6075.80', 'product': 'ALL', 'stat': 'Ok', 'cncSellCrditPrsnt': '0', 'debits': '243846.09', 'varmargin': '0.00', 'multiplier': '10.00', 'elm': '0.00', 'mfamount': '0.00', 'cashmarginavailable': '119428.29', 'brokeragePrsnt': '355.990260', 'cncRealizedMtomPrsnt': '0', 'notionalCash': '0.000000', 'directcollateralvalue': '0.00', 'cncBrokeragePrsnt': '0', 'valueindelivery': '0', 'nfoSpreadBenefit': '0', 'losslimit': '0', 'subtotal': '243846.09', 'rmsPayInAmnt': '0', 'unrealizedMtomPrsnt': '-0.00', 'coverOrderMarginPrsnt': '0', 'exchange': 'ALL', 'category': 'ABFS-COMMON', 'collateralvalue': '0.00', 'rmsIpoAmnt': '0', 'cncUnrealizedMtomPrsnt': '0', 'premiumPrsnt': '0'}, {'symbol': 'ALL', 'cncMarginUsed': '0', 'spanmargin': '0.00', 'branchAdhoc': '0.000000', 'adhocMargin': '0.000000', 'payoutamount': '0.00', 'cdsSpreadBenefit': '0', 'adhocscripmargin': '0.00', 'exposuremargin': '0.00', 'scripbasketmargin': '0.00', 'credits': '0.00', 'segment': 'COM', 'net': '0.00', 'turnover': '0.00', 'grossexposurevalue': '0.00', 'mfssAmountUsed': '0.00', 'realizedMtomPrsnt': '-0.00', 'product': 'ALL', 'stat': 'Ok', 'cncSellCrditPrsnt': '0', 'debits': '0.00', 'varmargin': '0.00', 'multiplier': '1.00', 'elm': '0.00', 'mfamount': '0.00', 'cashmarginavailable': '0.00', 'brokeragePrsnt': '0', 'cncRealizedMtomPrsnt': '0', 'notionalCash': '0.000000', 'directcollateralvalue': '0.00', 'cncBrokeragePrsnt': '0', 'valueindelivery': '0', 'nfoSpreadBenefit': '0', 'losslimit': '0', 'subtotal': '0.00', 'rmsPayInAmnt': '0', 'unrealizedMtomPrsnt': '-0.00', 'coverOrderMarginPrsnt': '0', 'exchange': 'ALL', 'category': 'NO_VAL', 'collateralvalue': '0.00', 'rmsIpoAmnt': '0', 'cncUnrealizedMtomPrsnt': '0', 'premiumPrsnt': '0'}]
```

### Get Profile
Code
```python
print(alice.get_profile()) # get profile
```
Sample response
```
{'accountStatus': 'Activated', 'dpType': 'CDSL', 'accountId': 'SP220xx', 'sBrokerName': 'ALICEBLUE', 'product': ['NRML', 'MIS', 'CNC', 'CO', 'BO'], 'accountName': 'xxxx xxxx', 'cellAddr': 'xxxxxxxxxx', 'emailAddr': 'xxxxxx@xxx.com', 'exchEnabled': 'bcs_fo|mcx_fo|nse_cm|bse_cm|nse_fo'}
```

### Get Daywise Positions
Code
```python
print(alice.get_daywise_positions()) # get daywise positions
```
Sample response
```
[{'realisedprofitloss': '-7,217.50', 'Fillsellamt': '292,062.50', 'Netqty': '0', 'Symbol': 'EICHERMOT', 'Instname': 'NA', 'Expdate': 'NA', 'LTP': '3,355.10', 'Opttype': 'XX', 'BLQty': 1.0, 'Token': '910', 'Fillbuyamt': '299,280.00', 'Fillsellqty': '87', 'Tsym': 'EICHERMOT-EQ', 'sSqrflg': 'Y', 'unrealisedprofitloss': '0.00', 'Buyavgprc': '3,440.00', 'MtoM': '-7,217.50', 'stat': 'Ok', 's_NetQtyPosConv': 'N', 'Sqty': '87', 'Sellavgprc': '3,357.04', 'PriceDenomenator': '1', 'PriceNumerator': '1', 'actid': 'SP220xx', 'posflag': 'true', 'Pcode': 'MIS', 'Stikeprc': '0', 'Bqty': '87', 'BEP': '0.00', 'Exchange': 'NSE', 'Series': 'EQ', 'GeneralDenomenator': '1', 'Type': 'DAY1', 'Netamt': '-7,217.50', 'companyname': 'EICHER MOTORS LTD', 'Fillbuyqty': '87', 'GeneralNumerator': '1', 'Exchangeseg': 'nse_cm', 'discQty': '10'}, {'realisedprofitloss': '1,141.70', 'Fillsellamt': '298,216.70', 'Netqty': '0', 'Symbol': 'M&M', 'Instname': 'NA', 'Expdate': 'NA', 'LTP': '1,274.65', 'Opttype': 'XX', 'BLQty': 1.0, 'Token': '2031', 'Fillbuyamt': '297,075.00', 'Fillsellqty': '233', 'Tsym': 'M&M-EQ', 'sSqrflg': 'Y', 'unrealisedprofitloss': '0.00', 'Buyavgprc': '1,275.00', 'MtoM': '1,141.70', 'stat': 'Ok', 's_NetQtyPosConv': 'N', 'Sqty': '233', 'Sellavgprc': '1,279.90', 'PriceDenomenator': '1', 'PriceNumerator': '1', 'actid': 'SP220xx', 'posflag': 'true', 'Pcode': 'MIS', 'Stikeprc': '0', 'Bqty': '233', 'BEP': '0.00', 'Exchange': 'NSE', 'Series': 'EQ', 'GeneralDenomenator': '1', 'Type': 'DAY1', 'Netamt': '1,141.70', 'companyname': 'MAHINDRA & MAHINDRA LTD', 'Fillbuyqty': '233', 'GeneralNumerator': '1', 'Exchangeseg': 'nse_cm', 'discQty': '10'}]
```

### Get Netwise Positions
Code
```python
print(alice.get_netwise_positions()) # get netwise positions
```
Sample response
```
[{'Instname': 'NA', 'Expdate': 'NA', 'CFsellqty': '0', 'Opttype': 'XX', 'Token': '910', 'CFSellavgprc': '0.00', 'sSqrflg': 'Y', 'unrealisedprofitloss': '0.00', 's_NetQtyPosConv': 'N', 'FillbuyamtCF': '0.00', 'Sqty': '87', 'Sellavgprc': '3,357.04', 'actid': 'SP220xx', 'netbuyamt': '299,280.00', 'Pcode': 'MIS', 'Bqty': '87', 'NetBuyavgprc': '3440.0', 'Exchange': 'NSE', 'companyname': 'EICHER MOTORS LTD', 'netbuyqty': '87', 'realisedprofitloss': '-7,217.50', 'Fillsellamt': '292,062.50', 'Netqty': '0', 'Symbol': 'EICHERMOT', 'LTP': '3,355.10', 'BLQty': 1.0, 'Fillbuyamt': '299,280.00', 'Fillsellqty': '87', 'Tsym': 'EICHERMOT-EQ', 'CFbuyqty': '0', 'Buyavgprc': '3,440.00', 'netSellamt': '292,062.50', 'MtoM': '-7,217.50', 'stat': 'Ok', 'FillsellamtCF': '0.00', 'PriceDenomenator': '1', 'netsellqty': '87', 'PriceNumerator': '1', 'posflag': 'true', 'Stikeprc': '0', 'BEP': '0.00', 'Series': 'EQ', 'GeneralDenomenator': '1', 'Type': 'DAY1', 'Netamt': '-7,217.50', 'NetSellavgprc': '3357.04', 'CFBuyavgprc': '0.00', 'Fillbuyqty': '87', 'GeneralNumerator': '1', 'Exchangeseg': 'nse_cm', 'discQty': '10'}, {'Instname': 'NA', 'Expdate': 'NA', 'CFsellqty': '0', 'Opttype': 'XX', 'Token': '2031', 'CFSellavgprc': '0.00', 'sSqrflg': 'Y', 'unrealisedprofitloss': '0.00', 's_NetQtyPosConv': 'N', 'FillbuyamtCF': '0.00', 'Sqty': '233', 'Sellavgprc': '1,279.90', 'actid': 'SP220xx', 'netbuyamt': '297,075.00', 'Pcode': 'MIS', 'Bqty': '233', 'NetBuyavgprc': '1275.0', 'Exchange': 'NSE', 'companyname': 'MAHINDRA & MAHINDRA LTD', 'netbuyqty': '233', 'realisedprofitloss': '1,141.70', 'Fillsellamt': '298,216.70', 'Netqty': '0', 'Symbol': 'M&M', 'LTP': '1,274.65', 'BLQty': 1.0, 'Fillbuyamt': '297,075.00', 'Fillsellqty': '233', 'Tsym': 'M&M-EQ', 'CFbuyqty': '0', 'Buyavgprc': '1,275.00', 'netSellamt': '298,216.70', 'MtoM': '1,141.70', 'stat': 'Ok', 'FillsellamtCF': '0.00', 'PriceDenomenator': '1', 'netsellqty': '233', 'PriceNumerator': '1', 'posflag': 'true', 'Stikeprc': '0', 'BEP': '0.00', 'Series': 'EQ', 'GeneralDenomenator': '1', 'Type': 'DAY1', 'Netamt': '1,141.70', 'NetSellavgprc': '1279.9', 'CFBuyavgprc': '0.00', 'Fillbuyqty': '233', 'GeneralNumerator': '1', 'Exchangeseg': 'nse_cm', 'discQty': '10'}, {'Instname': 'OPTIDX', 'Expdate': '1 Sep, 2022', 'CFsellqty': '0', 'Opttype': 'CE', 'Token': '51698', 'CFSellavgprc': '0.00', 'sSqrflg': 'Y', 'unrealisedprofitloss': '555.00', 's_NetQtyPosConv': 'N', 'FillbuyamtCF': '18,570.00', 'Sqty': '0', 'Sellavgprc': '0.00', 'actid': 'SP220xx', 'netbuyamt': '18,570.00', 'Pcode': 'NRML', 'Bqty': '0', 'NetBuyavgprc': '441.0', 'Exchange': 'NFO', 'companyname': '', 'netbuyqty': '50', 'realisedprofitloss': '0.00', 'Fillsellamt': '0.00', 'Netqty': '50', 'Symbol': 'BANKNIFTY', 'LTP': '382.50', 'BLQty': 25.0, 'Fillbuyamt': '0.00', 'Fillsellqty': '0', 'Tsym': 'BANKNIFTY2290139100CE', 'CFbuyqty': '50', 'Buyavgprc': '0.00', 'netSellamt': '0.00', 'MtoM': '555.00', 'stat': 'Ok', 'FillsellamtCF': '0.00', 'PriceDenomenator': '1', 'netsellqty': '0', 'PriceNumerator': '1', 'posflag': 'false', 'Stikeprc': '39100.0', 'BEP': '371.40', 'Series': 'XX', 'GeneralDenomenator': '1', 'Type': 'NET1', 'Netamt': '-18,570.00', 'NetSellavgprc': '0.00', 'CFBuyavgprc': '441.0', 'Fillbuyqty': '0', 'GeneralNumerator': '1', 'Exchangeseg': 'nse_fo', 'discQty': 'NA'}, {'Instname': 'OPTIDX', 'Expdate': '1 Sep, 2022', 'CFsellqty': '100', 'Opttype': 'CE', 'Token': '51731', 'CFSellavgprc': '128.45', 'sSqrflg': 'Y', 'unrealisedprofitloss': '-150.00', 's_NetQtyPosConv': 'N', 'FillbuyamtCF': '0.00', 'Sqty': '0', 'Sellavgprc': '0.00', 'actid': 'SP220xx', 'netbuyamt': '0.00', 'Pcode': 'NRML', 'Bqty': '0', 'NetBuyavgprc': '0.00', 'Exchange': 'NFO', 'companyname': '', 'netbuyqty': '0', 'realisedprofitloss': '0.00', 'Fillsellamt': '0.00', 'Netqty': '-100', 'Symbol': 'BANKNIFTY', 'LTP': '96.00', 'BLQty': 25.0, 'Fillbuyamt': '0.00', 'Fillsellqty': '0', 'Tsym': 'BANKNIFTY2290139900CE', 'CFbuyqty': '0', 'Buyavgprc': '0.00', 'netSellamt': '9,450.00', 'MtoM': '-150.00', 'stat': 'Ok', 'FillsellamtCF': '9,450.00', 'PriceDenomenator': '1', 'netsellqty': '100', 'PriceNumerator': '1', 'posflag': 'false', 'Stikeprc': '39900.0', 'BEP': '94.50', 'Series': 'XX', 'GeneralDenomenator': '1', 'Type': 'NET1', 'Netamt': '9,450.00', 'NetSellavgprc': '128.45', 'CFBuyavgprc': '0.00', 'Fillbuyqty': '0', 'GeneralNumerator': '1', 'Exchangeseg': 'nse_fo', 'discQty': 'NA'}]
```

### Get Holding Positions
Code
```python
print(alice.get_holding_positions()) # get holding positions
```
Sample response
```
{'stat': 'Ok', 'HoldingVal': [{'WCqty': '0', 'BSEHOldingValue': '25700.00', 'hsflag': 'Y', 'Series1': 'A', 'HUqty': '200', 'authQty': '0', 'YSXHOldingValue': '0.00', 'CSEHOldingValue': '0.00', 'Ttrind': 'N', 'DaysMTM': '0', 'csflag': 'Y', 'WHqty': '0', 'Pcode': 'CNC', 'Price': '102.78', 'Exch4': '0', 'BuyQty': '0', 'Bsetsym': 'BANKBARODA', 'Exch5': '0', 'LTcse': '0.00', 'MCXHOldingValue': '0.00', 'Holdqty': '0', 'Exch1': 'nse_cm', 'Exch2': 'bse_cm', 'Exch3': '0', 'LTysx': '0.00', 'Haircut': '0.00', 'Scripcode': '532134', 'LTPValuation': '0', 'NSEHOldingValue': '25660.00', 'Ysxtsym': '0', 'Ltp': '128.50', 'Coltype': '--', 'Btst': '0', 'LTmcxsxcm': '0.00', 'Usedqty': '0', 'poaStatus': 'Y', 'Token5': '0', 'Nsetsym': 'BANKBARODA-EQ', 'CUqty': '0', 'Token2': '532134', 'Token1': '4668', 'Token4': '0', 'Token3': '0', 'SellableQty': '200', 'Mcxsxcmsym': '0', 'Csetsym': '0', 'authFlag': True, 'LTnse': '128.30', 'pdc': '125.9', 'Series': 'EQ', 'Colqty': '0', 'ExchSeg5': None, 'ExchSeg2': 'BSE', 'ExchSeg1': 'NSE', 'LTbse': '128.50', 'ExchSeg4': None, 'ExchSeg3': None, 'isin': 'INE028A01039', 'Tprod': 'NA'}, {'WCqty': '0', 'BSEHOldingValue': '772832.75', 'hsflag': 'Y', 'Series1': 'X', 'HUqty': '19345', 'authQty': '0', 'YSXHOldingValue': '0.00', 'CSEHOldingValue': '0.00', 'Ttrind': 'N', 'DaysMTM': '0', 'csflag': 'Y', 'WHqty': '0', 'Pcode': 'CNC', 'Price': '44.60', 'Exch4': '0', 'BuyQty': '0', 'Bsetsym': 'SMIFS', 'Exch5': '0', 'LTcse': '0.00', 'MCXHOldingValue': '0.00', 'Holdqty': '0', 'Exch1': '0', 'Exch2': 'bse_cm', 'Exch3': '0', 'LTysx': '0.00', 'Haircut': '0.00', 'Scripcode': '508905', 'LTPValuation': '0', 'NSEHOldingValue': '0.00', 'Ysxtsym': '0', 'Ltp': '39.95', 'Coltype': '--', 'Btst': '0', 'LTmcxsxcm': '0.00', 'Usedqty': '0', 'poaStatus': 'Y', 'Token5': '0', 'Nsetsym': '0', 'CUqty': '0', 'Token2': '508905', 'Token1': '0', 'Token4': '0', 'Token3': '0', 'SellableQty': '19345', 'Mcxsxcmsym': '0', 'Csetsym': '0', 'authFlag': True, 'LTnse': '0.00', 'pdc': '41.95', 'Series': '---', 'Colqty': '0', 'ExchSeg5': None, 'ExchSeg2': 'BSE', 'ExchSeg1': None, 'LTbse': '39.95', 'ExchSeg4': None, 'ExchSeg3': None, 'isin': 'INE641A01013', 'Tprod': 'NA'}], 'clientid': 'WBK293', 'Totalval': {'TotalMCXHoldingValue': '0.00', 'TotalCSEHoldingValue': '0.00', 'TotalNSEHoldingValue': '25660.00', 'TotalYSXHoldingValue': '0.00', 'TotalBSEHoldingValue': '798532.75'}}
```

### Get master contracts
Getting master contracts allow you to search for instruments by symbol name and place orders.
Master contracts are stored as an OrderedDict by token number and by symbol name in a local file. Whenever you get a trade update, order update, or quote update, the library will check if master contracts are loaded. If they are, it will attach the instrument object directly to the update. By default all master contracts of all enabled exchanges in your personal profile will be downloaded. i.e. If your profile contains the following as enabled exchanges `['NSE', 'BSE', 'MCX', NFO']` all contract notes of all exchanges will be downloaded by default. If you feel it takes too much time to download all exchange, or if you don't need all exchanges to be downloaded, you can specify which exchange to download contract notes while creating the AliceBlue object. Master contracts once downloaded is stored in temp location and reused the subsequent times. Master contracts are downloaded newly once a day (because new master contracts are updated everyday around 8:00am).

Code
```python
alice = AliceBlue(username = "username", session_id = session_id, master_contracts_to_download=['NSE', 'BSE'])
```
This will reduce a few seconds in object creation time of AliceBlue object.

#### Get Scrip info
Get Scrip info from alice server (this is different from instrument object).
```python
print(alice.get_scrip_info(alice.get_instrument_by_symbol("NSE", "INFY-EQ")))
```
```
{'optiontype': 'XX', 'SQty': 55, 'vwapAveragePrice': '1499.38', 'LTQ': '40', 'Ltp': '1511.65', 'LTP': '1511.65', 'DecimalPrecision': 2, 'openPrice': '1488.00', 'BRate': '00.00', 'defmktproval': '3', 'BQty': 0, 'symbolname': 'INFY', 'noMktPro': '0', 'LTT': '09/09/2022 15:59:32', 'mktpro': '1', 'TickSize': '5', 'Multiplier': 1, 'strikeprice': '00.00', 'TotalSell': '55', 'High': '1520.00', 'stat': 'Ok', 'BodLotQty': 1, 'yearlyHighPrice': '1953.90', 'yearlyLowPrice': '1367.15', 'exchFeedTime': '09-Sep-2022 16:18:43', 'PrvClose': '1511.65', 'SRate': '1511.65', 'Change': '00.00', 'Series': 'EQ', 'TotalBuy': 'NA', 'Low': '1480.00', 'UniqueKey': 'INFY', 'PerChange': '00.00', 'companyname': 'INFOSYS LIMITED', 'TradeVolume': '4816910', 'TSymbl': 'INFY-EQ', 'Exp': 'NA', 'LTD': 'NA'}
```
#### Instrument object
Instruments are represented by instrument objects. These are named-tuples that are created while getting the master contracts. They are used when placing an order and subscribing to a symbol. The structure of an instrument tuple is as follows:

```python
Instrument = namedtuple('Instrument', ['exchange', 'token', 'symbol',
                                      'name', 'expiry', 'lot_size'])
```

All instruments have the fields mentioned above. Wherever a field is not applicable for an instrument (for example, equity instruments don't have strike prices), that value will be `None`.

### Get tradable instruments
Symbols can be retrieved in multiple ways. Once you have the master contract loaded for an exchange, you can get an instrument in many ways.

#### Get a single instrument by it's name:
Code
```python
tatasteel_nse_eq = alice.get_instrument_by_symbol('NSE', 'TATASTEEL-EQ')
reliance_nse_eq = alice.get_instrument_by_symbol('NSE', 'RELIANCE-EQ')
ongc_bse_eq = alice.get_instrument_by_symbol('BSE', 'ONGC-EQ')
india_vix_nse_index = alice.get_instrument_by_symbol('NSE', 'India VIX')
sensex_nse_index = alice.get_instrument_by_symbol('BSE', 'SENSEX')
nifty50_nse_index = alice.get_instrument_by_symbol('NSE', 'NIFTY 50')
banknifty_nse_index = alice.get_instrument_by_symbol('NSE', 'NIFTY Bank')
```

#### Get a single instrument by it's token number (generally useful only for BSE Equities):
Code
```python
ongc_bse_eq = alice.get_instrument_by_token('BSE', 500312)
reliance_bse_eq = alice.get_instrument_by_token('BSE', 500325)
acc_nse_eq = alice.get_instrument_by_token('NSE', 22)
```

#### Get FNO instruments easily by mentioning expiry, strike & call or put.
Code
```python
bn_fut = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2019, 6, 27), is_fut=True, strike=None, is_CE = False)
bn_call = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2019, 6, 27), is_fut=False, strike=30000, is_CE = True)
bn_put = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2019, 6, 27), is_fut=False, strike=30000, is_CE = False)
```

### Search for symbols
Search for multiple instruments by matching the name. This works case insensitive and returns all instrument which has the name in its symbol.
Code
```python
all_sensex_scrips = alice.search_instruments('BSE', 'sEnSeX')
print(all_sensex_scrips)
```
The above code results multiple symbol which has 'sensex' in its symbol.
Sample response
```
[Instrument(exchange='BSE', token=532985, symbol='KTKSENSEX', name='KOTAK MAHINDRA MUTUAL FUND', expiry=None, lot_size='1'), Instrument(exchange='BSE', token=535276, symbol='SBISENSEX', name='SBI MUTUAL FUND - SBI ETF SENS', expiry=None, lot_size='1'), Instrument(exchange='BSE', token=538683, symbol='SENSEXBEES', name='NIPPON INDIA ETF SENSEX', expiry=None, lot_size='1'), Instrument(exchange='BSE', token=540154, symbol='IDFSENSEXE', name='IDFC Mutual Fund', expiry=None, lot_size='1'), Instrument(exchange='BSE', token=199040, symbol='SENSEXBINAV', name='INAV NIPPO INDIA ETF SENSE', expiry=None, lot_size='1')]
```

#### Search for multiple instruments by matching multiple names
Code
```python
multiple_underlying = ["INFY", "SBIN", "BHEL"]
all_scripts = alice.search_instruments('NFO', multiple_underlying)
print(all_scripts)
```

### Live Feed Data and Market Depth Data
Once you have master contracts loaded & a tradable instrument, you can easily subscribe to market feedd/depth data.

#### Two types of Live data are available
You can subscribe any one type of live data for a given scrip. Using the `LiveFeedType` enum, you can specify what type of live feed you need.
* `LiveFeedType.TICK_DATA`
* `LiveFeedType.DEPTH_DATA`

Please refer to the original documentation [here](https://v2api.aliceblueonline.com/websocket) for more details of different types of live feeds.

#### Subscribe to a live feed
Code
```python
alice.subscribe(alice.get_instrument_by_symbol('NSE', 'TATASTEEL-EQ'), LiveFeedType.TICK_DATA)
alice.subscribe(alice.get_instrument_by_symbol('BSE', 'RELIANCE-EQ'), LiveFeedType.DEPTH_DATA)
```
#### Subscribe to multiple instruments in a single call. Give an array of instruments to be subscribed.
Code
```python
alice.subscribe([alice.get_instrument_by_symbol('NSE', 'TATASTEEL-EQ'), alice.get_instrument_by_symbol('NSE', 'ACC-EQ')], LiveFeedType.TICK_DATA)
```

#### Start getting live feed via websocket
Code
```python
def event_handler_quote_update(message):
    print(f"quote update {message}")

alice.start_websocket(subscribe_callback=event_handler_quote_update)

alice.subscribe(alice.get_instrument_by_symbol('NSE', 'ONGC-EQ'), LiveFeedType.TICK_DATA)
sleep(10)
```

#### Unsubscribe to a live feed
Unsubscribe to an existing live feed.

Code
```python
alice.unsubscribe(alice.get_instrument_by_symbol('NSE', 'TATASTEEL-EQ'), LiveFeedType.TICK_DATA)
alice.unsubscribe(alice.get_instrument_by_symbol('BSE', 'RELIANCE-EQ'), LiveFeedType.DEPTH_DATA)
```
#### Unsubscribe to multiple instruments in a single call. Give an array of instruments to be unsubscribed.
Code
```python
alice.unsubscribe([alice.get_instrument_by_symbol('NSE', 'TATASTEEL-EQ'), alice.get_instrument_by_symbol('NSE', 'ACC-EQ')], LiveFeedType.TICK_DATA)
```

#### Get All Subscribed Symbols
Code
```python
alice.get_all_subscriptions() # All
```

### Market Status messages & Exchange messages.
Subscribe to market status & Exchange messages coming soon.

#### Subscribe to Market Status messages
Code
```python
alice.subscribe_market_status_messages()
```

#### Getting market status messages.
Code
```python
print(alice.get_market_status_messages())
```

Sample Response of `get_market_status_messages()`
```
[{'exchange': 'NSE', 'length_of_market_type': 6, 'market_type': b'NORMAL', 'length_of_status': 31, 'status': b'The Closing Session has closed.'}, {'exchange': 'NFO', 'length_of_market_type': 6, 'market_type': b'NORMAL', 'length_of_status': 45, 'status': b'The Normal market has closed for 22 MAY 2020.'}, {'exchange': 'CDS', 'length_of_market_type': 6, 'market_type': b'NORMAL', 'length_of_status': 45, 'status': b'The Normal market has closed for 22 MAY 2020.'}, {'exchange': 'BSE', 'length_of_market_type': 13, 'market_type': b'OTHER SESSION', 'length_of_status': 0, 'status': b''}]
```

#### Subscribe to exchange messages
Code
```python
alice.subscribe_exchange_messages()
```

#### Getting market status messages.
Code
```python
print(alice.get_exchange_messages())
```

Sample Response of `get_exchange_messages()`
```
[{'exchange': 'NSE', 'length': 32, 'message': b'DS : Bulk upload can be started.', 'exchange_time_stamp': 1590148595}, {'exchange': 'NFO', 'length': 200, 'message': b'MARKET WIDE LIMIT FOR VEDL IS 183919959. OPEN POSITIONS IN VEDL HAVE REACHED 84 PERCENT OF THE MARKET WIDE LIMIT.                                                                                       ', 'exchange_time_stamp': 1590146132}, {'exchange': 'CDS', 'length': 54, 'message': b'DS : Regular segment Bhav copy broadcast successfully.', 'exchange_time_stamp': 1590148932}, {'exchange': 'MCX', 'length': 7, 'message': b'.......', 'exchange_time_stamp': 1590196159}]
```

#### Market Status messages & Exchange messages through callbacks
Code
```python
socket_opened = False
def market_status_messages(message):
    print(f"market status messages {message}")

def exchange_messages(message):
    print(f"exchange messages {message}")

alice.start_websocket(market_status_messages_callback=market_status_messages,
                      exchange_messages_callback=exchange_messages)
alice.subscribe_market_status_messages()
alice.subscribe_exchange_messages()
sleep(10)
```

### Place an order
You can place following types of order through this API.
1. [Limit](#limit-order-intraday-buy)
1. [Market](#market-order-delivery-sell)
1. [Stop Loss Limit](#stop-loss-limit-order)
1. [Stop Loss Market](#stop-loss-market-order)
1. [Bracket Order](#bracket-order)
1. [AMO](#after-market-order)

#### Limit Order (Intraday Buy)
Code
```python
print(alice.place_order(transaction_type = TransactionType.Buy, 
                        instrument = alice.get_instrument_by_symbol("NSE", "INFY-EQ"), 
                        quantity = 1,
                        order_type = OrderType.Limit, 
                        product_type = ProductType.Intraday, 
                        price = 500.0))
```
Sample reponse of place order
```python
[{'stat': 'Ok', 'NOrdNo': '220909000171482'}]
```
#### Market Order (Delivery Sell)

```python
print(alice.place_order(transaction_type = TransactionType.Sell,
                        instrument = alice.get_instrument_by_symbol("NSE", "INFY-EQ"), 
                        quantity = 0, 
                        order_type = OrderType.Market, 
                        product_type = ProductType.Delivery))
```

#### Stop Loss Limit order 
```python
print(alice.place_order(transaction_type = TransactionType.Sell, 
                        instrument = alice.get_instrument_by_symbol("NSE", "INFY-EQ"), 
                        quantity = 1, 
                        order_type = OrderType.StopLossLimit,
                        product_type = ProductType.Intraday, 
                        price = 500.0, 
                        trigger_price = 490.0))
```
#### Stop Loss Market order 
```python
print(alice.place_order(transaction_type = TransactionType.Sell, 
                        instrument = alice.get_instrument_by_symbol("NSE", "INFY-EQ"), 
                        quantity = 1, 
                        order_type = OrderType.StopLossMarket,
                        product_type = ProductType.Intraday, 
                        trigger_price = 490.0))
```
#### Bracket Order
```python
print(alice.place_order(transaction_type = TransactionType.Sell,
                        instrument = alice.get_instrument_by_symbol("NSE", "INFY-EQ"), 
                        quantity = 1, 
                        order_type = OrderType.StopLossLimit,
                        product_type = ProductType.Intraday, 
                        price = 1464.0, 
                        trigger_price = 1466.0, 
                        stop_loss = 1450.0, 
                        target = 1480.0, 
                        trailing_sl = 1.0))
```
#### After Market Order
Code
```python
print(alice.place_order(transaction_type = TransactionType.Buy, 
                        instrument = alice.get_instrument_by_symbol("NSE", "INFY-EQ"), 
                        quantity = 1, 
                        order_type = OrderType.AfterMarketOrder,
                        product_type = ProductType.Delivery, 
                        price = 500.0))
```
Sample reponse of AMO order
```
[{'stat': 'Ok', 'NOrdNo': '220909000171690-after market order req received'}]
```
#### Modify Order
```python
print(alice.modify_order(   order_id = order_id, 
                            transaction_type = TransactionType.Buy, 
                            instrument = alice.get_instrument_by_symbol("NSE", "INFY-EQ"), 
                            quantity = 2, 
                            order_type = OrderType.AfterMarketOrder,
                            product_type = ProductType.Delivery, 
                            price = 600.0))
```
Sample response of modify order
```
{'stat': 'Ok', 'Result': ' NEST Order Number :220909000171761'}
```

#### Cancel an order
```python
order_id = 220909000171761
print(alice.cancel_order(order_id = order_id))
```
Sample response of cancel order
```
{'stat': 'Ok', 'Result': ' NEST Order Number :220909000171761'}
```

### Getting order history and trade details

#### Get order history of all orders.
```python
print(alice.get_order_history())
```
```
[{'Prc': '600.00', 'RequestID': '1', 'Cancelqty': 0, 'discQtyPerc': '10', 'customText': 'NA', 'Mktpro': 'NA', 'defmktproval': '3', 'optionType': 'XX', 'usecs': '078218', 'mpro': '1', 'Qty': 2, 'ordergenerationtype': 'AMO', 'Unfilledsize': 0, 'orderAuthStatus': '', 'Usercomments': 'NA', 'ticksize': '5', 'Prctype': 'AMO', 'Status': 'cancelled after market order', 'Minqty': 0, 'orderCriteria': 'NA', 'Exseg': 'nse_cm', 'Sym': 'INFY', 'multiplier': '1', 'ExchOrdID': 'NA', 'ExchConfrmtime': '--', 'Pcode': 'CNC', 'SyomOrderId': '', 'Dscqty': 0, 'Exchange': 'NSE', 'Ordvaldate': 'NA', 'accountId': 'SP220xx', 'exchangeuserinfo': '111111111111130', 'Avgprc': '00.00', 'Trgprc': '00.00', 'Trantype': 'B', 'bqty': '1', 'Trsym': 'INFY-EQ', 'Fillshares': 0, 'AlgoCategory': 'NA', 'sipindicator': 'N', 'strikePrice': '00.00', 'reporttype': 'NA', 'AlgoID': 'NA', 'noMktPro': '0', 'BrokerClient': '--', 'OrderUserMessage': '', 'decprec': '2', 'ExpDate': 'NA', 'COPercentage': 0.0, 'marketprotectionpercentage': '--', 'Nstordno': '220909000171761', 'ExpSsbDate': 'NA', 'OrderedTime': '09/09/2022 15:47:11', 'RejReason': '--', 'modifiedBy': 'SP220xx', 'Scripname': 'INFOSYS LIMITED', 'stat': 'Ok', 'orderentrytime': '', 'PriceDenomenator': '1', 'panNo': 'NA', 'RefLmtPrice': 0.0, 'PriceNumerator': '1', 'token': '1594', 'ordersource': 'NEST_REST_WEB', 'Validity': None, 'GeneralDenomenator': '1', 'series': 'EQ', 'InstName': '', 'GeneralNumerator': '1', 'user': 'SP220xx', 'remarks': '--', 'iSinceBOE': 1662718631}, {'Prc': '378.50', 'RequestID': '1', 'Cancelqty': 0, 'discQtyPerc': '10', 'customText': 'NA', 'Mktpro': 'NA', 'defmktproval': '3', 'optionType': 'XX', 'usecs': '428162', 'mpro': '1', 'Qty': 704, 'ordergenerationtype': '--', 'Unfilledsize': 0, 'orderAuthStatus': '', 'Usercomments': 'NA', 'ticksize': '5', 'Prctype': 'L', 'Status': 'complete', 'Minqty': 0, 'orderCriteria': 'NA', 'Exseg': 'nse_cm', 'Sym': 'HINDALCO', 'multiplier': '1', 'ExchOrdID': '1100000000211421', 'ExchConfrmtime': '09-Sep-2022 09:07:03', 'Pcode': 'MIS', 'SyomOrderId': '', 'Dscqty': 0, 'Exchange': 'NSE', 'Ordvaldate': 'NA', 'accountId': 'SP220xx', 'exchangeuserinfo': '333333333333100', 'Avgprc': '426.00', 'Trgprc': '00.00', 'Trantype': 'S', 'bqty': '1', 'Trsym': 'HINDALCO-EQ', 'Fillshares': 704, 'AlgoCategory': 'NA', 'sipindicator': 'N', 'strikePrice': '00.00', 'reporttype': 'fill', 'AlgoID': 'NA', 'noMktPro': '0', 'BrokerClient': '--', 'OrderUserMessage': '', 'decprec': '2', 'ExpDate': 'NA', 'COPercentage': 0.0, 'marketprotectionpercentage': '--', 'Nstordno': '220909000001363', 'ExpSsbDate': 'NA', 'OrderedTime': '09/09/2022 09:07:03', 'RejReason': '--', 'modifiedBy': '--', 'Scripname': 'HINDALCO  INDUSTRIES  LTD', 'stat': 'Ok', 'orderentrytime': 'Sep 09 2022 09:06:59', 'PriceDenomenator': '1', 'panNo': 'xxxxx', 'RefLmtPrice': 0.0, 'PriceNumerator': '1', 'token': '1363', 'ordersource': 'NEST_REST_TLAPI', 'Validity': 'DAY', 'GeneralDenomenator': '1', 'series': 'EQ', 'InstName': '', 'GeneralNumerator': '1', 'user': 'SP220xx', 'remarks': '--', 'iSinceBOE': 1662694623}]
```

#### Get order history of a particular order
```python
print(alice.get_order_history(220909000171761))
```
Sample Response
```
[{'Prc': '600.00', 'Action': 'B', 'productcode': 'CNC', 'reporttype': 'NA', 'triggerprice': '0.0', 'filledShares': 0, 'disclosedqty': '0', 'exchangetimestamp': '--', 'ExchTimeStamp': '09/09/2022 15:47:11', 'symbolname': 'INFY', 'nestordernumber': '220909000171761', 'duration': None, 'OrderUserMessage': '', 'averageprice': '0.0', 'Qty': 2, 'ordergenerationtype': 'AMO', 'modifiedBy': 'SP220xx', 'filldateandtime': '-- --', 'Status': 'cancelled after market order', 'rejectionreason': '--', 'stat': 'Ok', 'PriceDenomenator': '1', 'exchangeorderid': None, 'PriceNumerator': '1', 'legorderindicator': '', 'customerfirm': 'C', 'ordersource': 'NEST_REST_WEB', 'GeneralDenomenator': '1', 'nestreqid': '1', 'Ordtype': 'AMO', 'unfilledSize': 0, 'scripname': 'INFOSYS LIMITED', 'GeneralNumerator': '1', 'bqty': 1, 'exchange': 'NSE', 'Trsym': 'INFY-EQ'}, {'Prc': '600.00', 'Action': 'B', 'productcode': 'CNC', 'reporttype': 'NA', 'triggerprice': '0.0', 'filledShares': 0, 'disclosedqty': '0', 'exchangetimestamp': '--', 'ExchTimeStamp': '09/09/2022 15:47:10', 'symbolname': 'INFY', 'nestordernumber': '220909000171761', 'duration': None, 'OrderUserMessage': '', 'averageprice': '0.0', 'Qty': 2, 'ordergenerationtype': 'AMO', 'modifiedBy': 'SP220xx', 'filldateandtime': '-- --', 'Status': 'modify after market order req received', 'rejectionreason': '--', 'stat': 'Ok', 'PriceDenomenator': '1', 'exchangeorderid': None, 'PriceNumerator': '1', 'legorderindicator': '', 'customerfirm': 'C', 'ordersource': 'NEST_REST_WEB', 'GeneralDenomenator': '1', 'nestreqid': '1', 'Ordtype': 'AMO', 'unfilledSize': 2, 'scripname': 'INFOSYS LIMITED', 'GeneralNumerator': '1', 'bqty': 1, 'exchange': 'NSE', 'Trsym': 'INFY-EQ'}, {'Prc': '500.00', 'Action': 'B', 'productcode': 'CNC', 'reporttype': 'NA', 'triggerprice': '0.0', 'filledShares': 0, 'disclosedqty': '1', 'exchangetimestamp': '--', 'ExchTimeStamp': '09/09/2022 15:47:09', 'symbolname': 'INFY', 'nestordernumber': '220909000171761', 'duration': 'DAY', 'OrderUserMessage': '', 'averageprice': '0.0', 'Qty': 1, 'ordergenerationtype': 'AMO', 'modifiedBy': '--', 'filldateandtime': '-- --', 'Status': 'after market order req received', 'rejectionreason': '--', 'stat': 'Ok', 'PriceDenomenator': '1', 'exchangeorderid': None, 'PriceNumerator': '1', 'legorderindicator': '', 'customerfirm': 'C', 'ordersource': 'NEST_REST_WEB', 'GeneralDenomenator': '1', 'nestreqid': '1', 'Ordtype': 'AMO', 'unfilledSize': 1, 'scripname': 'INFOSYS LIMITED', 'GeneralNumerator': '1', 'bqty': 1, 'exchange': 'NSE', 'Trsym': 'INFY-EQ'}]
```

#### Get trade book
```python
print(alice.get_trade_book())
```
Sample Response
```
[{'Filltime': '15:10:00', 'usecs': '836064', 'Ordduration': 'DAY', 'ExchordID': '1100000022855645', 'Qty': 201, 'ordergenerationtype': '--', 'strikeprice': '00.00', 'AvgPrice': '1499.52', 'Prctype': 'MKT', 'Minqty': 0, 'Exchseg': 'nse_cm', 'Pcode': 'MIS', 'FillLeg': 1, 'Exchange': 'NSE', 'accountId': 'SP220xx', 'Price': '1499.40', 'Trantype': 'S', 'companyname': 'HDFC BANK LTD', 'Exchtime': '09-Sep-2022 15:10:00', 'bqty': 1, 'Filldate': '09-Sep-2022', 'AlgoCategory': 'NA', 'Custofrm': 'C', 'expdate': 'NA', 'optiontype': 'XX', 'AlgoID': 'NA', 'Symbol': '1333', 'Filledqty': 201, 'Time': '09/09/2022 15:10:00', 'symbolname': 'HDFCBANK', 'BrokerClient': '--', 'NOReqID': '1', 'Tsym': 'HDFCBANK-EQ', 'Nstordno': '220909000161876', 'ReportType': 'fill', 'Expiry': 'NA', 'stat': 'Ok', 'PriceDenomenator': '1', 'panNo': 'xxxxxxxxx', 'PriceNumerator': '1', 'posflag': 'false', 'GeneralDenomenator': '1', 'FillId': '29599427', 'Fillqty': 29, 'series': 'EQ', 'GeneralNumerator': '1', 'user': 'SP220xx', 'remarks': '--', 'iSinceBOE': 1662716400}, {'Filltime': '15:10:00', 'usecs': '835977', 'Ordduration': 'DAY', 'ExchordID': '1100000022855645', 'Qty': 201, 'ordergenerationtype': '--', 'strikeprice': '00.00', 'AvgPrice': '1499.55', 'Prctype': 'MKT', 'Minqty': 0, 'Exchseg': 'nse_cm', 'Pcode': 'MIS', 'FillLeg': 1, 'Exchange': 'NSE', 'accountId': 'SP220xx', 'Price': '1499.55', 'Trantype': 'S', 'companyname': 'HDFC BANK LTD', 'Exchtime': '09-Sep-2022 15:10:00', 'bqty': 1, 'Filldate': '09-Sep-2022', 'AlgoCategory': 'NA', 'Custofrm': 'C', 'expdate': 'NA', 'optiontype': 'XX', 'AlgoID': 'NA', 'Symbol': '1333', 'Filledqty': 162, 'Time': '09/09/2022 15:10:00', 'symbolname': 'HDFCBANK', 'BrokerClient': '--', 'NOReqID': '1', 'Tsym': 'HDFCBANK-EQ', 'Nstordno': '220909000161876', 'ReportType': 'fill', 'Expiry': 'NA', 'stat': 'Ok', 'PriceDenomenator': '1', 'panNo': 'xxxxxxxxx', 'PriceNumerator': '1', 'posflag': 'false', 'GeneralDenomenator': '1', 'FillId': '29599425', 'Fillqty': 162, 'series': 'EQ', 'GeneralNumerator': '1', 'user': 'SP220xx', 'remarks': '--', 'iSinceBOE': 1662716400}, {'Filltime': '15:10:00', 'usecs': '836021', 'Ordduration': 'DAY', 'ExchordID': '1100000022855645', 'Qty': 201, 'ordergenerationtype': '--', 'strikeprice': '00.00', 'AvgPrice': '1499.54', 'Prctype': 'MKT', 'Minqty': 0, 'Exchseg': 'nse_cm', 'Pcode': 'MIS', 'FillLeg': 1, 'Exchange': 'NSE', 'accountId': 'SP220xx', 'Price': '1499.45', 'Trantype': 'S', 'companyname': 'HDFC BANK LTD', 'Exchtime': '09-Sep-2022 15:10:00', 'bqty': 1, 'Filldate': '09-Sep-2022', 'AlgoCategory': 'NA', 'Custofrm': 'C', 'expdate': 'NA', 'optiontype': 'XX', 'AlgoID': 'NA', 'Symbol': '1333', 'Filledqty': 172, 'Time': '09/09/2022 15:10:00', 'symbolname': 'HDFCBANK', 'BrokerClient': '--', 'NOReqID': '1', 'Tsym': 'HDFCBANK-EQ', 'Nstordno': '220909000161876', 'ReportType': 'fill', 'Expiry': 'NA', 'stat': 'Ok', 'PriceDenomenator': '1', 'panNo': 'xxxxxxxxx', 'PriceNumerator': '1', 'posflag': 'false', 'GeneralDenomenator': '1', 'FillId': '29599426', 'Fillqty': 10, 'series': 'EQ', 'GeneralNumerator': '1', 'user': 'SP220xx', 'remarks': '--', 'iSinceBOE': 1662716400}]
```

### Order properties as enums
Order properties such as TransactionType, OrderType, and others have been safely classified as enums so you don't have to write them out as strings.

#### TransactionType
Transaction types indicate whether you want to buy or sell. Valid transaction types are of the following:

* `TransactionType.Buy` - buy
* `TransactionType.Sell` - sell

#### OrderType
Order type specifies the type of order you want to send. Valid order types include:

* `OrderType.Market` - Place the order with a market price
* `OrderType.Limit` - Place the order with a limit price (limit price parameter is mandatory)
* `OrderType.StopLossLimit` - Place as a stop loss limit order
* `OrderType.StopLossMarket` - Place as a stop loss market order
* `OrderType.BracketOrder` - Place as a bracket order
* `OrderType.AfterMarketOrder` - Place as a after market order

#### ProductType
Product types indicate the complexity of the order you want to place. Valid product types are:

* `ProductType.Intraday` - Intraday order that will get squared off before market close
* `ProductType.Delivery` - Delivery order that will be held with you after market close

## Example strategy using alice blue API
[Here](https://gist.github.com/krishnavelu/e0df312ccf5f022edb1823461ff4230e) is an example moving average strategy using alice blue API.
This strategy generates a buy signal when 5-EMA > 20-EMA (golden cross) or a sell signal when 5-EMA < 20-EMA (death cross).

## Historical API
Alice Blue now supports downloading historical data for back testing.
1. Historical data API will be available from 5:30 PM (evening) to 8 AM (Next day morning) on weekdays (Monday to Friday). Historical data will not be available during market hours
1. Historical data API will be available fully during weekends and holidays.
1. For NSE segment, 2 years of historical data will be provided.
1. For NFO, CDS and MCX segments, current expiry data will be provided.

Code
```python
print(alice.historical_data(alice.get_instrument_by_symbol("NSE", "INFY-EQ"),
                            datetime.datetime.now(), 
                            datetime.datetime.now(), 
                            HistoricalDataType.Minute))
```
Sample Reponse
```
{'stat': 'Ok', 'result': [{'volume': 130792.0, 'high': 1489.8, 'low': 1483.1, 'time': '2022-09-09 09:15:00', 'close': 1488.8, 'open': 1488.0}, {'volume': 33730.0, 'high': 1488.95, 'low': 1485.35, 'time': '2022-09-09 09:16:00', 'close': 1486.0, 'open': 1488.05}, {'volume': 28446.0, 'high': 1486.5, 'low': 1484.0, 'time': '2022-09-09 09:17:00', 'close': 1484.8, 'open': 1485.65}, {'volume': 33256.0, 'high': 1486.0, 'low': 1484.55, 'time': '2022-09-09 09:18:00', 'close': 1485.45, 'open': 1484.9}], 'message': None}
```
## Read this before creating an issue
Before creating an issue in this library, please follow the following steps.

1. Search the problem you are facing is already asked by someone else. There might be some issues already there, either solved/unsolved related to your problem. Go to [issues](https://github.com/krishnavelu/alice_blue/issues) page, use `is:issue` as filter and search your problem. ![image](https://user-images.githubusercontent.com/38440742/85207058-376ee400-b2f4-11ea-91ad-c8fd8a682a12.png)
2. If you feel your problem is not asked by anyone or no issues are related to your problem, then create a new issue.
3. Describe your problem in detail while creating the issue. If you don't have time to detail/describe the problem you are facing, assume that I also won't be having time to respond to your problem.
4. Post a sample code of the problem you are facing. If I copy paste the code directly from issue, I should be able to reproduce the problem you are facing.
5. Before posting the sample code, test your sample code yourself once. Only sample code should be tested, no other addition should be there while you are testing.
6. Have some print() function calls to display the values of some variables related to your problem.
7. Post the results of print() functions also in the issue.
8. Use the insert code feature of github to inset code and print outputs, so that the code is displayed neat. ![image](https://user-images.githubusercontent.com/38440742/85207234-4dc96f80-b2f5-11ea-990c-df013dd69cf2.png)
9. If you have multiple lines of code, use triple grave accent ( ``` ) to insert multiple lines of code. [Example:](https://docs.github.com/en/github/writing-on-github/creating-and-highlighting-code-blocks) ![image](https://user-images.githubusercontent.com/38440742/89105781-343a3e00-d3f2-11ea-9f86-92dda88aa5bf.png)
10. [Here](https://github.com/krishnavelu/alice_blue/issues/134#issuecomment-647016659) is an example of what I'm expecting while you are creating an issue.
