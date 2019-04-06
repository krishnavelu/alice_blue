
# Python SDK for Alice Blue API

The Python library for communicating with the Alice Blue APIs.

Alice Blue Python library provides an easy to use wrapper over the HTTPs APIs.

The HTTP calls have been converted to methods and JSON responses are wrapped into Python-compatible objects.

Websocket connections are handled automatically within the library

## Disclaimer
* At the time of this writing, this is the only python library available to support Alice Blue trading APIs. This is not an official release from Alice Blue itself. 
* Author of this library is no way commercially linked with broker Alice Blue.
* This library is released with an intention of public contribution. 
* Author of this library is not resposible for any amout of losses incurred by using this library.

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

### Prerequisites

Python 3.x

Also, you need the following modules:

* `protlib`
* `websocket_client`
* `requests`
* `bs4`

The modules can also be installed using `pip`

## Getting started with API

### Overview
There is only one class in the whole library: `AliceBlue`. The `login_and_get_access_token()` static method is used to retrieve an access token from the alice blue server. An access token is valid for 24 hours.
With an access token, you can instantiate an AliceBlue object. Ideally you only need to create an access_token once every day. After you have the access token, you can store it
separately for re-use.

### REST Documentation
The original REST API that this SDK is based on is available online.
   [Alice Blue API REST documentation](http://antplus.aliceblueonline.com/#introduction)

## Using the API

### Logging
The whole library is equipped with python's `logging` moduele for debugging. If more debug information is needed, enable logging using the following code.
  
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Get an access token
1. Import alice_blue
```python
from alice_blue import *
```

2. Create access_token using login_and_get_access_token() function  with your `username`, `password`, `2FA` and `api_secret`
```python
access_token = AliceBlue.login_and_get_access_token(username='username', password='password', twoFA='a',  api_secret='api_secret')
```

### Create AliceBlue Object
1. Once you have your `access_token`, you can create an AliceBlue object with your `access_token`, `username` and `password`.
```python
alice = AliceBlue(username='username', password='password', access_token=access_token)
```

2. You can run commands here to check your connectivity
```python
print(alice.get_balance()) # get balance / margin limits
print(alice.get_profile()) # get profile
print(alice.get_daywise_positions()) # get daywise positions
print(alice.get_netwise_positions()) # get netwise positions
print(alice.get_holding_positions()) # get holding positions
```

### Get master contracts
Getting master contracts allow you to search for instruments by symbol name and place orders.
Master contracts are stored as an OrderedDict by token number and by symbol name. Whenever you get a trade update, order update, or quote update, the library will check if master contracts are loaded. If they are, it will attach the instrument object directly to the update. By default all master contracts of all enabled exchanges in your personal profile will be downloaded. i.e. If your profile contains the folowing as enabled exchanges `['NSE', 'BSE', 'MCX', NFO']` all contract notes of all exchanges will be downloaded by default. If you feel it takes too much time to download all exchange, or if you don't need all exchanges to be downloaded, you can specify which exchange to download contract notes while creating the AliceBlue object.

```python
alice = AliceBlue(username='username', password='password', access_token=access_token, master_contracts_to_download=['NSE', 'BSE'])
```
This will reduce a few milliseconds in object creation time of AliceBlue object.


### Search for symbols
Symbols can be retrieved in multiple ways. Once you have the master contract loaded for an exchange, you can search for an instrument in many ways.

Search for a single instrument by it's name:
```python
tatasteel_nse_eq = alice.get_instrument_by_symbol('NSE', 'TATASTEEL')
reliance_nse_eq = alice.get_instrument_by_symbol('NSE', 'RELIANCE')
ongc_bse_eq = alice.get_instrument_by_symbol('BSE', 'ONGC')
india_vix_nse_index = alice.get_instrument_by_symbol('NSE', 'India VIX')
sensex_nse_index = alice.get_instrument_by_symbol('BSE', 'Sensex')
```

Search for a single instrument by it's token number (generally useful only for BSE Equities):
```python
ongc_bse_eq = alice.get_instrument_by_token(500312)
reliance_bse_eq = alice.get_instrument_by_token(500325)
acc_nse_eq = alice.get_instrument_by_token(22)
```

Search for multiple instruments by matching the name
```python
all_banknifty_scrips = alice.search_instruments('NFO', 'BANKNIFTY')
```

Search FNO instruments easily by mentioning expiry, strike & call or put.
```python
bn_fut = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2019, 6, 27), is_fut=True, strike=None, is_CE = False)
bn_call = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2019, 6, 27), is_fut=False, strike=30000, is_CE = True)
bn_put = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2019, 6, 27), is_fut=False, strike=30000, is_CE = False)
```


#### Instrument object
Instruments are represented by instrument objects. These are named-tuples that are created while getting the master contracts. They are used when placing an order and searching for an instrument. The structure of an instrument tuple is as follows:
```python
Instrument = namedtuple('Instrument', ['exchange', 'token', 'symbol',
                                      'name', 'expiry', 'lot_size'])
```

All instruments have the fields mentioned above. Wherever a field is not applicable for an instrument (for example, equity instruments don't have strike prices), that value will be `None`

### Quote update
Once you have master contracts loaded, you can easily subscribe to quote updates.

#### Four types of feed data are available
You can subscribe any one type of quote update for a given scrip. Using the `LiveFeedType` enum, you can specify what type of live feed you need.
* `LiveFeedType.MARKET_DATA`
* `LiveFeedType.COMPACT`
* `LiveFeedType.SNAPQUOTE`
* `LiveFeedType.FULL_SNAPQUOTE`

Please refer to the original documentation [here](http://antplus.aliceblueonline.com/#marketdata) for more details of different types of quote update.


#### Subscribe to a live feed
```python
alice.subscribe(alice.get_instrument_by_symbol('NSE', 'TATASTEEL'), LiveFeedType.MARKET_DATA)
alice.subscribe(alice.get_instrument_by_symbol('BSE', 'RELIANCE'), LiveFeedType.COMPACT)
```
Subscribe to multiple instruments in a single call. Give an array of instruments to be subscribed.

```python
alice.subscribe([alice.get_instrument_by_symbol('NSE', 'TATASTEEL'), alice.get_instrument_by_symbol('NSE', 'ACC')], LiveFeedType.MARKET_DATA)
```

Start getting live feed via socket

```python
socket_opened = False
def event_handler_quote_update(message):
    print(f"quote update {message}")

def open_callback():
    global socket_opened
    socket_opened = True

alice.start_websocket(subscribe_callback=event_handler_quote_update,
                      socket_open_callback=open_callback,
                      run_in_background=True)
while(socket_opened==False):
    pass
alice.subscribe(alice.get_instrument_by_symbol('NSE', 'ONGC'), LiveFeedType.MARKET_DATA)
sleep(10)
```

#### Unsubscribe to a live feed
Unsubscribe to an existing live feed
```python
alice.unsubscribe(alice.get_instrument_by_symbol('NSE', 'TATASTEEL'), LiveFeedType.MARKET_DATA)
alice.unsubscribe(alice.get_instrument_by_symbol('BSE', 'RELIANCE'), LiveFeedType.COMPACT)
```
Unsubscribe to multiple instruments in a single call. Give an array of instruments to be unsubscribed.
```python
alice.unsubscribe([alice.get_instrument_by_symbol('NSE', 'TATASTEEL'), alice.get_instrument_by_symbol('NSE', 'ACC')], LiveFeedType.MARKET_DATA)
```

#### Get All Subscribed Symbols
```python
alice.get_all_subscriptions() # All
```

### Place an order
Place limit, market, SL, SL-M, AMO, BO, CO orders

```python
print (alice.get_profile())

# TransactionType.Buy, OrderType.Market, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%1%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.Delivery,
                     price = 0.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
   )

# TransactionType.Buy, OrderType.Market, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%2%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.Intraday,
                     price = 0.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)

# TransactionType.Buy, OrderType.Market, ProductType.CoverOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%3%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Market,
                     product_type = ProductType.CoverOrder,
                     price = 0.0,
                     trigger_price = 7.5, # trigger_price Here the trigger_price is taken as stop loss (provide stop loss in actual amount)
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)


# TransactionType.Buy, OrderType.Limit, ProductType.BracketOrder
# OCO Order can't be of type market

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%4%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.BracketOrder,
                     price = 8.0,
                     trigger_price = None,
                     stop_loss = 6.0,
                     square_off = 10.0,
                     trailing_sl = None,
                     is_amo = False)
)

# TransactionType.Buy, OrderType.Limit, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%5%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.Intraday,
                     price = 8.0,
                     trigger_price = None,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)


# TransactionType.Buy, OrderType.Limit, ProductType.CoverOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%6%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.Limit,
                     product_type = ProductType.CoverOrder,
                     price = 7.0,
                     trigger_price = 6.5, # trigger_price Here the trigger_price is taken as stop loss (provide stop loss in actual amount)
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)

###############################

# TransactionType.Buy, OrderType.StopLossMarket, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%7%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Delivery,
                     price = 0.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)


# TransactionType.Buy, OrderType.StopLossMarket, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%8%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Intraday,
                     price = 0.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)



# TransactionType.Buy, OrderType.StopLossMarket, ProductType.CoverOrder
# CO order is of type Limit and And Market Only

# TransactionType.Buy, OrderType.StopLossMarket, ProductType.BO
# BO order is of type Limit and And Market Only

###################################

# TransactionType.Buy, OrderType.StopLossLimit, ProductType.Delivery

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%9%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossMarket,
                     product_type = ProductType.Delivery,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)


# TransactionType.Buy, OrderType.StopLossLimit, ProductType.Intraday

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%10%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.Intraday,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
)



# TransactionType.Buy, OrderType.StopLossLimit, ProductType.CoverOrder
# CO order is of type Limit and And Market Only


# TransactionType.Buy, OrderType.StopLossLimit, ProductType.BracketOrder

print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%11%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(
   alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = alice.get_instrument_by_symbol('NSE', 'INFY'),
                     quantity = 1,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.BracketOrder,
                     price = 8.0,
                     trigger_price = 8.0,
                     stop_loss = 1.0,
                     square_off = 1.0,
                     trailing_sl = 20,
                     is_amo = False)
)
```

### Cancel an order

```python
alice.cancel_order('170713000075481') #Cancel an open order
```

### Order properties as enums
Order properties such as TransactionType, OrderType, and others have been safely classified as enums so you don't have to write them out as strings

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

#### ProductType
Product types indicate the complexity of the order you want to place. Valid product types are:

* `ProductType.Intraday` - Intraday order that will get squared off before market close
* `ProductType.Delivery` - Delivery order that will be held with you after market close
* `ProductType.CoverOrder` - Cover order
* `ProductType.BracketOrder` - One cancels other order. Also known as bracket order
