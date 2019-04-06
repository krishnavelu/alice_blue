import json
import requests
import threading
import websocket
import logging
import enum
import datetime
from time import sleep
from bs4 import BeautifulSoup
from collections import OrderedDict
from protlib import CUInt, CStruct, CULong, CUChar, CArray
from collections import namedtuple

Instrument = namedtuple('Instrument', ['exchange', 'token', 'symbol',
                                       'name', 'expiry', 'lot_size'])

class Requests(enum.Enum):
    PUT = 1
    DELETE = 2
    GET = 3
    POST = 4

class TransactionType(enum.Enum):
    Buy = 'BUY'
    Sell = 'SELL'

class OrderType(enum.Enum):
    Market = 'MARKET'
    Limit = 'LIMIT'
    StopLossLimit = 'SL'
    StopLossMarket = 'SLM'

class ProductType(enum.Enum):
    Intraday = 'I'
    Delivery = 'D'
    CoverOrder = 'CO'
    BracketOrder = 'BO'

class LiveFeedType(enum.Enum):
    MARKET_DATA = 1
    COMPACT = 2
    SNAPQUOTE = 3
    FULL_SNAPQUOTE = 4

class WsFrameMode(enum.IntEnum):
    MARKETDATA          =    1
    COMPACT_MARKETDATA  =    2
    SNAPQUOTE           =    3
    FULL_SNAPQUOTE      =    4
    SPREADDATA          =    5
    SPREAD_SNAPQUOTE    =    6
    DPR                 =    7
    OI                  =    8
    MARKET_STATUS       =    9
    EXCHANGE_MESSAGES   =    10
    
class MarketData(CStruct):
    exchange = CUChar()
    token = CUInt()
    ltp = CUInt()
    ltt = CUInt()
    ltq = CUInt()
    volume = CUInt()
    best_bid_price = CUInt()
    best_bid_quantity = CUInt()
    best_ask_price = CUInt()
    best_ask_quantity = CUInt()
    total_buy_quantity = CULong()
    total_sell_quantity = CULong()
    atp = CUInt()
    exchange_time_stamp = CUInt()
    open = CUInt()
    high = CUInt()
    low = CUInt()
    close = CUInt()
    yearly_high = CUInt()
    yearly_low = CUInt()
        
class CompactData(CStruct):
    exchange = CUChar()
    token = CUInt()
    ltp = CUInt()
    change = CUInt()
    exchange_time_stamp = CUInt()
    volume = CUInt()
     
class SnapQuote(CStruct):
    exchange = CUChar()
    token = CUInt()
    buyers = CArray(5, CUInt)
    bid_prices = CArray(5, CUInt)
    bid_quantities = CArray(5, CUInt)
    sellers = CArray(5, CUInt)
    ask_prices = CArray(5, CUInt)
    ask_quantities = CArray(5, CUInt)
    exchange_time_stamp = CUInt()
 
class FullSnapQuote(CStruct):
    exchange = CUChar()
    token = CUInt()
    buyers = CArray(5, CUInt)
    bid_prices = CArray(5, CUInt)
    bid_quantities = CArray(5, CUInt)
    sellers = CArray(5, CUInt)
    ask_prices = CArray(5, CUInt)
    ask_quantities = CArray(5, CUInt)
    atp = CUInt()
    open = CUInt()
    high = CUInt()
    low = CUInt()
    close = CUInt()
    total_buy_quantity = CULong()
    total_sell_quantity = CULong()
    volume = CUInt()

class DPR(CStruct):
    exchange = CUChar()
    token = CUInt()
    exchange_time_stamp = CUInt()
    high = CUInt()
    low = CUInt()

class OpenInterest(CStruct):
    exchange = CUChar()
    token = CUInt()
    current_open_interest = CUChar()
    initial_open_interest = CUChar()
    exchange_time_stamp = CUInt()

# class ExchangeMessage(CStruct):
#     exchange = CUChar()
#     length = CUShort()
#     message = CString()
#     exchange_time_stamp = CUInt()
# 
# class MarketStatus(CStruct):
#     exchange = CUChar()
#     length_of_market_type = CUShort()
#     market_type = CString()
#     length_of_status = CUShort()
#     status = CString()
#     exchange_time_stamp = CUInt()

class AliceBlue:
    # dictionary object to hold settings
    __service_config = {
      'host': 'https://ant.aliceblueonline.com',
      'routes': {
          'authorize': '/oauth2/auth',
          'access_token': '/oauth2/token',
          'profile': '/api/v2/profile',
          'master_contract': '/api/v2/contracts.json?exchanges={exchange}',
          'holdings': '/api/v2/holdings',
          'balance': '/api/v2/cashposition',
          'positions_daywise': '/api/v2/positions?type=daywise',
          'positions_netwise': '/api/v2/positions?type=netwise',
          'positions_holdings': '/api/v2/holdings',
          'place_order': '/api/v2/order',
          'place_amo': '/api/v2/amo',
          'place_bracket_order': '/api/v2/bracketorder',
          'place_basket_order' : '/api/v2/basketorder',
          'get_orders': '/api/v2/order',
          'get_order_info': '/api/v2/order/{order_id}',
          'modify_order': '/api/v2/order',
          'cancel_order': '/api/v2/order?oms_order_id={order_id}&order_status=open',
          'trade_book': '/api/v2/trade',
      },
      'socket_endpoint': 'wss://ant.aliceblueonline.com/hydrasocket/v2/websocket?access_token={access_token}'
    }

    def __init__(self, username, password, access_token, master_contracts_to_download = None):
        """ logs in and gets enabled exchanges and products for user """
        self.__access_token = access_token
        self.__username = username
        self.__password = password
        self.__websocket = None
        self.__ws_mutex = threading.Lock()
        self.__on_error = None
        self.__on_disconnect = None
        self.__on_open = None
        self.__subscribe_callback = None
        self.__order_update_callback = None
        self.__subscribers = {}
        self.__exchange_codes = {'NSE' : 1,
                                 'NFO' : 2,
                                 'CDS' : 3,
                                 'MCX' : 4,
                                 'BSE' : 6,
                                 'BFO' : 7}
        self.__exchange_price_multipliers = {1: 100,
                                             2: 100,
                                             3: 10000000,
                                             4: 100,
                                             6: 100,
                                             7: 100}

        try:
            profile = self.__api_call_helper('profile', Requests.GET, None, None)
        except Exception as e:
            logging.info(f"Couldn't get profile info with credentials provided {e}")
            return
        if('error' in profile):
            logging.info(f"Couldn't get profile info {profile['message']}")
            return
        self.__enabled_exchanges = profile['data']['exchanges']
        self.__master_contracts_by_token = {}
        self.__master_contracts_by_symbol = {}
        if(master_contracts_to_download == None):
            for e in self.__enabled_exchanges:
                self.__get_master_contract(e)
        else:
            for e in master_contracts_to_download:
                if(e in self.__enabled_exchanges):
                    self.__get_master_contract(e)
        self.ws_thread = None

    @staticmethod
    def login_and_get_access_token(username, password, twoFA, api_secret, redirect_url='https://ant.aliceblueonline.com/plugin/callback'):
        #Get the Code
        r = requests.Session()
        config = AliceBlue.__service_config
        resp = r.get(f"{config['host']}{config['routes']['authorize']}?response_type=code&state=test_state&client_id={username}&redirect_uri={redirect_url}")
        if('OAuth 2.0 Error' in resp.text):
            logging.info("OAuth 2.0 Error occurred. Please verify your api_secret")
            return None
        page = BeautifulSoup(resp.text, features="html.parser")
        csrf_token = page.find('input', attrs = {'name':'_csrf_token'})['value']
        login_challenge = page.find('input', attrs = {'name' : 'login_challenge'})['value']
        resp = r.post(resp.url,data={'client_id':username,'password':password,'login_challenge':login_challenge,'_csrf_token':csrf_token})
        if('Please Enter Valid Password' in resp.text):
            logging.info("Please enter a valid password")
            return
        if('Internal server error' in resp.text):
            logging.info("Got Internal server error, please try again after sometimes")
            return
        question_ids = []
        page = BeautifulSoup(resp.text, features="html.parser")
        err = page.find('p', attrs={'class':'error'})
        if(len(err) > 0):
            logging.info(f"Couldn't login {err}")
            return
        for i in page.find_all('input', attrs={'name':'question_id1'}):
            question_ids.append(i['value'])
        logging.info(f"Assuming answers for all 2FA questions are '{twoFA}', Please change it to '{twoFA}' if not")
        resp = r.post(resp.url,data={'answer1':twoFA,'question_id1':question_ids,'answer2':twoFA,'login_challenge':login_challenge,'_csrf_token':csrf_token})
        code = resp.url[resp.url.index('=')+1:resp.url.index('&')]

        #Get Access Token
        params = {'code': code, 'redirect_uri': redirect_url, 'grant_type': 'authorization_code', 'client_secret' : api_secret, "cliend_id": username}
        url = f"{config['host']}{config['routes']['access_token']}?client_id={username}&client_secret={api_secret}&grant_type=authorization_code&code={code}&redirect_uri={redirect_url}&authorization_response=authorization_response"
        resp = r.post(url,auth=(username, api_secret),data=params)
        resp = json.loads(resp.text)
        if('access_token' in resp):
            access_token = resp['access_token']
            logging.info(f'access_token - {access_token}')
            return access_token
        else:
            logging.info(f"Couldn't get access token {resp}")
        return None

    def __convert_prices(self, dictionary, multiplier):
        keys = ['ltp', 
                'best_bid_price',
                'best_ask_price',
                'atp',
                'open',
                'high',
                'low',
                'close',
                'yearly_high',
                'yearly_low']
        for key in keys:
            if(key in dictionary):
                dictionary[key] = dictionary[key]/multiplier
        multiple_value_keys = ['bid_prices', 'ask_prices']
        for key in multiple_value_keys:
            if(key in dictionary):
                new_values = []
                for value in dictionary[key]:
                    new_values.append(value/multiplier)
                dictionary[key] = new_values
        return dictionary
    
    def __conver_exchanges(self, dictionary):
        d = self.__exchange_codes
        dictionary['exchange'] = list(d.keys())[list(d.values()).index(dictionary['exchange'])]
        return dictionary

    def __convert_instrument(self, dictionary):
        dictionary['instrument'] = self.get_instrument_by_token( dictionary['token'])
        return dictionary
        
    def __modify_human_readable_values(self, dictionary):
        dictionary = self.__convert_prices(dictionary, self.__exchange_price_multipliers[dictionary['exchange']])
        dictionary = self.__conver_exchanges(dictionary)
        dictionary = self.__convert_instrument(dictionary)
        return dictionary

    def __on_data_callback(self, message, data_type, continue_flag):
        if(message[0] == WsFrameMode.MARKETDATA):
            p = MarketData.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p) 
            if(self.__subscribe_callback is not None):
                self.__subscribe_callback(res)
        elif(message[0] == WsFrameMode.COMPACT_MARKETDATA):
            p = CompactData.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p) 
            if(self.__subscribe_callback is not None):
                self.__subscribe_callback(res)
        elif(message[0] == WsFrameMode.SNAPQUOTE):
            p = SnapQuote.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p) 
            if(self.__subscribe_callback is not None):
                self.__subscribe_callback(res)
        elif(message[0] == WsFrameMode.FULL_SNAPQUOTE):
            p = FullSnapQuote.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p)
            if(self.__subscribe_callback is not None):
                self.__subscribe_callback(res)
        elif(message[0] == WsFrameMode.DPR):
            p = DPR.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p) 
        elif(message[0] == WsFrameMode.OI):
            p = OpenInterest.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p) 
        elif(message[0] == WsFrameMode.MARKET_STATUS):
            logging.info(f"market status {message}")
#             p = MarketStatus.parse(message[1:]).__dict__
#             res = self.__modify_human_readable_values(p) 
            return
        elif(message[0] == WsFrameMode.EXCHANGE_MESSAGES):
            logging.info(f"exchange message {message}")
#             p = ExchangeMessage.parse(message[1:]).__dict__
#             res = self.__modify_human_readable_values(p) 
            return
         
    def __on_close_callback(self):
        if self.__on_disconnect:
            self.__on_disconnect()

    def __on_open_callback(self):
        if self.__on_open:
            self.__on_open()

    def __on_error_callback(self, error):
        if self.__on_error:
            self.__on_error(error)

    def __send_heartbeat(self):
        heart_beat = {"a": "h", "v": [], "m": ""}
        while True:
            sleep(10)
            with self.__ws_mutex:
                self.__websocket.send(json.dumps(heart_beat), opcode = websocket._abnf.ABNF.OPCODE_PING)

    def start_websocket(self, subscribe_callback = None, 
                                order_update_callback = None,
                                socket_open_callback = None,
                                socket_close_callback = None,
                                socket_error_callback = None,
                                run_in_background=False):
        self.__on_open = socket_open_callback
        self.__on_disconnect = socket_close_callback
        self.__on_error = socket_error_callback
        self.__subscribe_callback = subscribe_callback
        self.__order_update_callback = order_update_callback
        
        url = self.__service_config['socket_endpoint'].format(access_token=self.__access_token)
        self.__websocket = websocket.WebSocketApp(url,
                                                on_data=self.__on_data_callback,
                                                on_error=self.__on_error_callback,
                                                on_close=self.__on_close_callback,
                                                on_open=self.__on_open_callback)
        th = threading.Thread(target=self.__send_heartbeat)
        th.daemon = True
        th.start()
        if run_in_background is True:
            self.__ws_thread = threading.Thread(target=self.__websocket.run_forever)
            self.__ws_thread.daemon = True
            self.__ws_thread.start()
        else:
            self.__websocket.run_forever()

    def get_profile(self):
        return self.__api_call_helper('profile', Requests.GET, None, None)

    def get_balance(self):
        return self.__api_call_helper('balance', Requests.GET, None, None)

    def get_daywise_positions(self):
        return self.__api_call_helper('positions_daywise', Requests.GET, None, None)

    def get_netwise_positions(self):
        return self.__api_call_helper('positions_netwise', Requests.GET, None, None)

    def get_holding_positions(self):
        return self.__api_call_helper('positions_holdings', Requests.GET, None, None)

    def get_order_history(self, order_id=None):
        """ leave order_id as None to get all entire order history """
        if order_id is None:
            return self.__api_call_helper('get_orders', Requests.GET, None, None);
        else:
            return self.__api_call_helper('get_order_info', Requests.GET, {'order_id': order_id}, None);

    def get_trade_book(self):
        """ get all trades """
        return self.__api_call_helper('trade_book', Requests.GET, None, None)

    def get_exchanges(self):
        return self.__enabled_exchanges

    def place_order(self, transaction_type, instrument, quantity, order_type,
                    product_type, price=0.0, trigger_price=None,
                    stop_loss=None, square_off=None, trailing_sl=None,
                    is_amo = False):
        """ placing an order, many fields are optional and are not required
            for all order types
        """
        if transaction_type is None:
            raise TypeError("Required parameter transaction_type not of type TransactionType")

        if not isinstance(instrument, Instrument):
            raise TypeError("Required parameter instrument not of type Instrument")

        if not isinstance(quantity, int):
            raise TypeError("Required parameter quantity not of type int")

        if order_type is None:
            raise TypeError("Required parameter order_type not of type OrderType")

        if product_type is None:
            raise TypeError("Required parameter product_type not of type ProductType")

        if price is not None and not isinstance(price, float):
            raise TypeError("Optional parameter price not of type float")

        if trigger_price is not None and not isinstance(trigger_price, float):
            raise TypeError("Optional parameter trigger_price not of type float")

        if(product_type == ProductType.Intraday):
            product_type = 'MIS'
        elif(product_type == ProductType.Delivery):
            if(instrument.exchange == 'NFO'):
                product_type = 'NRML'
            else:
                product_type = 'CNC'
        elif(product_type == ProductType.CoverOrder):
            product_type = 'CO'
        elif(product_type == ProductType.BracketOrder):
            product_type = None
        # construct order object after all required parameters are met
        order = {  'exchange': instrument.exchange,
                   'order_type': order_type.value,
                   'instrument_token': instrument.token,
                   'quantity':quantity,
                   'disclosed_quantity':0,
                   'price':price,
                   'transaction_type':transaction_type.value,
                   'trigger_price':trigger_price,
                   'validity':'DAY',
                   'product':product_type,
                   'source':'web',
                   'order_tag': 'order1'}

        if stop_loss is not None and not isinstance(stop_loss, float):
            raise TypeError("Optional parameter stop_loss not of type float")
        elif stop_loss is not None:
            order['stop_loss_value'] = stop_loss

        if square_off is not None and not isinstance(square_off, float):
            raise TypeError("Optional parameter square_off not of type float")
        elif square_off is not None:
            order['square_off_value'] = square_off

        if trailing_sl is not None and not isinstance(trailing_sl, int):
            raise TypeError("Optional parameter trailing_sl not of type int")
        elif trailing_sl is not None:
            order['trailing_stop_loss'] = trailing_sl

        if product_type is ProductType.CoverOrder:
            if not isinstance(trigger_price, float):
                raise TypeError("Required parameter trigger_price not of type float")

        if product_type is ProductType.BracketOrder:
            helper = 'place_bracket_order'
            del order['product'] 
            if not isinstance(stop_loss, float):
                raise TypeError("Required parameter stop_loss not of type float")

            if not isinstance(square_off, float):
                raise TypeError("Required parameter square_off not of type float")
            
        if(is_amo == True):
            helper = 'place_amo'
        else:
            helper = 'place_order'
        return self.__api_call_helper(helper, Requests.POST, None, order)

    def modify_order(self, transaction_type, instrument, product_type, order_id, order_type, quantity=None, price=0.0,
                     trigger_price=0.0):
        """ modify an order, only order id is required, rest are optional, use only when
            when you want to change that attribute
        """
        if not isinstance(instrument, Instrument):
            raise TypeError("Required parameter instrument not of type Instrument")

        if not isinstance(order_id, str):
            raise TypeError("Required parameter order_id not of type str")

        if quantity is not None and not isinstance(quantity, int):
            raise TypeError("Optional parameter quantity not of type int")

        if type(order_type) is not OrderType:
            raise TypeError("Optional parameter order_type not of type OrderType")

        if ProductType is None:
            raise TypeError("Required parameter product_type not of type ProductType")

        if price is not None and not isinstance(price, float):
            raise TypeError("Optional parameter price not of type float")

        if trigger_price is not None and not isinstance(trigger_price, float):
            raise TypeError("Optional parameter trigger_price not of type float")

        if(product_type == ProductType.Intraday):
            product_type = 'MIS'
        elif(product_type == ProductType.Delivery):
            if(instrument.exchange == 'NFO'):
                product_type = 'NRML'
            else:
                product_type = 'CNC'
        elif(product_type == ProductType.CoverOrder):
            product_type = 'CO'
        elif(product_type == ProductType.BracketOrder):
            product_type = None
        # construct order object with order id
        order = {  'oms_order_id': str(order_id),  
                   'instrument_token': int(instrument.token),
                   'exchange': instrument.exchange,
                   'transaction_type':transaction_type.value,
                   'product':product_type,
                   'validity':'DAY',
                   'order_type': order_type.value,
                   'price':price,
                   'trigger_price':trigger_price,
                   'quantity':quantity,
                   'disclosed_quantity':0}
        return self.__api_call_helper('modify_order', Requests.PUT, None, order)

    def cancel_order(self, order_id):
        return self.__api_call_helper('cancel_order', Requests.DELETE, {'order_id': order_id}, None)

    def subscribe(self, instrument, live_feed_type):
        """ subscribe to the current feed of an instrument """
        if(type(live_feed_type) is not LiveFeedType):
            raise TypeError("Required parameter live_feed_type not of type LiveFeedType")
        arr = []
        if (isinstance(instrument, list)):
            for _instrument in instrument:
                if not isinstance(_instrument, Instrument):
                    raise TypeError("Required parameter instrument not of type Instrument")
                exchange = self.__exchange_codes[_instrument.exchange] 
                if _instrument.exchange not in self.__enabled_exchanges:
                    logging.warning(f'Invalid exchange value provided: {_instrument.exchange}')
                    raise TypeError(f"Please provide a valid exchange {self.__enabled_exchanges})")
                arr.append([exchange, int(_instrument.token)])
                self.__subscribers[_instrument.token] = live_feed_type
        else:
            if not isinstance(instrument, Instrument):
                raise TypeError("Required parameter instrument not of type Instrument")
            exchange = self.__exchange_codes[instrument.exchange]
            arr = [[exchange, int(instrument.token)]]
            self.__subscribers[instrument.token] = live_feed_type
        if(live_feed_type == LiveFeedType.MARKET_DATA):
            mode = 'marketdata' 
        elif(live_feed_type == LiveFeedType.COMPACT):
            mode = 'compact_marketdata' 
        elif(live_feed_type == LiveFeedType.SNAPQUOTE):
            mode = 'snapquote' 
        elif(live_feed_type == LiveFeedType.FULL_SNAPQUOTE):
            mode = 'full_snapquote' 
        data = json.dumps({'a' : 'subscribe', 'v' : arr, 'm' : mode})
        with self.__ws_mutex:
            ret = self.__websocket.send(data)
        return ret

    def unsubscribe(self, instrument, live_feed_type):
        """ subscribe to the current feed of an instrument """
        if(type(live_feed_type) is not LiveFeedType):
            raise TypeError("Required parameter live_feed_type not of type LiveFeedType")
        arr = []
        if (isinstance(instrument, list)):
            for _instrument in instrument:
                if not isinstance(_instrument, Instrument):
                    raise TypeError("Required parameter instrument not of type Instrument")
                exchange = self.__exchange_codes[_instrument.exchange] 
                if _instrument.exchange not in self.__enabled_exchanges:
                    logging.warning(f'Invalid exchange value provided: {_instrument.exchange}')
                    raise TypeError(f"Please provide a valid exchange {self.__enabled_exchanges})")
                arr.append([exchange, int(_instrument.token)])
                if(_instrument.token in self.__subscribers): del self.__subscribers[_instrument.token]
        else:
            if not isinstance(instrument, Instrument):
                raise TypeError("Required parameter instrument not of type Instrument")
            exchange = self.__exchange_codes[instrument.exchange]
            arr = [[exchange, int(instrument.token)]]
            if(instrument.token in self.__subscribers): del self.__subscribers[instrument.token]
        if(live_feed_type == LiveFeedType.MARKET_DATA):
            mode = 'marketdata' 
        elif(live_feed_type == LiveFeedType.COMPACT):
            mode = 'compact_marketdata' 
        elif(live_feed_type == LiveFeedType.SNAPQUOTE):
            mode = 'snapquote' 
        elif(live_feed_type == LiveFeedType.FULL_SNAPQUOTE):
            mode = 'full_snapquote' 
        data = json.dumps({'a' : 'unsubscribe', 'v' : arr, 'm' : mode})
        with self.__ws_mutex:
            ret = self.__websocket.send(data)
        return ret

    def get_all_subscriptions(self):
        """ get the current feed of an instrument """
        res = {}
        for key, value in self.__subscribers.items():
            ins = self.get_instrument_by_token(key)
            res[ins] = value
        return res

    def get_instrument_by_symbol(self, exchange, symbol):
        # get instrument given exchange and symbol
        exchange = exchange.upper()
        # check if master contract exists
        if exchange not in self.__master_contracts_by_symbol:
            logging.warning(f"Cannot find exchange {exchange} in master contract. "
                            "Please ensure if that exchange is enabled in your profile and downloaded the master contract for the same")
            return None
        master_contract = self.__master_contracts_by_symbol[exchange]
        if symbol not in master_contract:
            logging.warning(f"Cannot find symbol {exchange} {symbol} in master contract")
            return None
        return master_contract[symbol]
    
    def get_instrument_for_fno(self, symbol, expiry_date, is_fut=False, strike=None, is_CE = False):
        res = self.search_instruments('NFO', symbol)
        matches = []
        for i in res:
            if(i.expiry == expiry_date):
                matches.append(i)
        for i in matches:
            if(is_fut == True):
                if('FUT' in i.symbol):
                    return i
            else:
                sp = i.symbol.split(' ')
                if(len(sp) == 4):           # Only option scrips 
                    if(sp[2] == str(strike)):
                        if(is_CE == True):
                            if(sp[-1] == 'CE'):
                                return i
                        else:
                            if(sp[-1] == 'PE'):
                                return i
                            
    def search_instruments(self, exchange, symbol):
        # search instrument given exchange and symbol
        exchange = exchange.upper()
        matches = []
        # check if master contract exists
        if exchange not in self.__master_contracts_by_token:
            logging.warning(f"Cannot find exchange {exchange} in master contract. "
                "Please ensure if that exchange is enabled in your profile and downloaded the master contract for the same")
            return None
        master_contract = self.__master_contracts_by_token[exchange]
        for contract in master_contract:
            if symbol in master_contract[contract].symbol:
                matches.append(master_contract[contract])
        return matches

    def get_instrument_by_token(self, token):
        if(type(token) is int):
            token = str(token)
        for _, lst in self.__master_contracts_by_token.items():
            for key, value in lst.items():
                if token == key:
                    return value
        return None

    def get_master_contract(self, exchange):
        return self.__master_contracts_by_symbol[exchange]

    def __get_master_contract(self, exchange):
        """ returns all the tradable contracts of an exchange
            placed in an OrderedDict and the key is the token
        """
        exchange = exchange.upper()
        if exchange not in self.__enabled_exchanges:
            logging.warning(f'Invalid exchange value provided: {exchange}, enabled exchanges for your account are {self.__enabled_exchanges}')
            raise ValueError(f"Please provide a valid exchange {self.__enabled_exchanges}")

        logging.debug(f'Downloading master contracts for exchange: {exchange}')
        body = self.__api_call_helper('master_contract', Requests.GET, {'exchange': exchange}, None)
        master_contract_by_token = OrderedDict()
        master_contract_by_symbol = OrderedDict()
        for sub in body:
            for scrip in body[sub]:
                # convert token
                token = scrip['code']
    
                # convert symbol to upper
                symbol = scrip['symbol']
    
                # convert expiry to none if it's non-existent
                if('expiry' in scrip):
                    expiry = datetime.datetime.fromtimestamp(scrip['expiry']).date()
                else:
                    expiry = None
    
                # convert lot size to int
                if('lotSize' in scrip):
                    lot_size = scrip['lotSize']
                else:
                    lot_size = None
                    
                # Name & Exchange 
                name = scrip['company'] 
                exch = scrip['exchange']
    
                instrument = Instrument(exch, token, symbol, name, expiry, lot_size)
                master_contract_by_token[token] = instrument
                master_contract_by_symbol[symbol] = instrument
        self.__master_contracts_by_token[exchange] = master_contract_by_token
        self.__master_contracts_by_symbol[exchange] = master_contract_by_symbol

    def __api_call_helper(self, name, http_method, params, data):
        # helper formats the url and reads error codes nicely
        config = self.__service_config
        url = f"{config['host']}{config['routes'][name]}"
        if params is not None:
            url = url.format(**params)
        response = self.__api_call(url, http_method, data)
        if response.status_code != 200:
            raise requests.HTTPError(response.text)
        return json.loads(response.text)

    def __api_call(self, url, http_method, data):
        headers = {"Content-Type": "application/json", "client_id": self.__username,
                   "authorization": f"Bearer {self.__access_token}"}
        #logging.debug('url:: %s http_method:: %s data:: %s headers:: %s', url, http_method, data, headers)
        r = None
        if http_method is Requests.POST:
            r = requests.post(url, data=json.dumps(data), headers=headers)
        elif http_method is Requests.DELETE:
            r = requests.delete(url, headers=headers)
        elif http_method is Requests.PUT:
            r = requests.put(url, data=json.dumps(data), headers=headers)
        elif http_method is Requests.GET:
            r = requests.get(url, headers=headers)
        return r
