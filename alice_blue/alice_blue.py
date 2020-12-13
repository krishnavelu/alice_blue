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
from protlib import CUInt, CStruct, CULong, CUChar, CArray, CUShort, CString
from collections import namedtuple

Instrument = namedtuple('Instrument', ['exchange', 'token', 'symbol',
                                       'name', 'expiry', 'lot_size'])
logger = logging.getLogger(__name__)

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
    StopLossMarket = 'SL-M'

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

class ExchangeMessage(CStruct):
    exchange = CUChar()
    length = CUShort()
    message = CString(length = "length")
    exchange_time_stamp = CUInt()
 
class MarketStatus(CStruct):
    exchange = CUChar()
    length_of_market_type = CUShort()
    market_type = CString(length = "length_of_market_type")
    length_of_status = CUShort()
    status = CString(length = "length_of_status")

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
          'cancel_bo_order': '/api/v2/order?oms_order_id={order_id}&order_status=open&leg_order_indicator={leg_order_id}',
          'cancel_co_order': '/api/v2/coverorder?oms_order_id={order_id}&order_status=open&leg_order_indicator={leg_order_id}',
          'trade_book': '/api/v2/trade',
          'scripinfo': '/api/v2/scripinfo?exchange={exchange}&instrument_token={token}',
      },
      'socket_endpoint': 'wss://ant.aliceblueonline.com/hydrasocket/v2/websocket?access_token={access_token}'
    }

    def __init__(self, username, password, access_token, master_contracts_to_download = None):
        """ logs in and gets enabled exchanges and products for user """
        self.__access_token = access_token
        self.__username = username
        self.__password = password
        self.__websocket = None
        self.__websocket_connected = False
        self.__ws_mutex = threading.Lock()
        self.__on_error = None
        self.__on_disconnect = None
        self.__on_open = None
        self.__subscribe_callback = None
        self.__order_update_callback = None
        self.__market_status_messages_callback = None
        self.__exchange_messages_callback = None
        self.__oi_callback = None
        self.__dpr_callback = None
        self.__subscribers = {}
        self.__market_status_messages = []
        self.__exchange_messages = []
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
            profile = self.get_profile()
        except Exception as e:
            raise Exception(f"Couldn't get profile info with credentials provided '{e}'")
        if(profile['status'] == 'error'):
            if(profile['message'] == 'Not able to retrieve AccountInfoService'):     # Don't know why this error comes, but it safe to proceed further.
                logger.warning("Couldn't get profile info - 'Not able to retrieve AccountInfoService'")
            else:
                raise Exception(f"Couldn't get profile info '{profile['message']}'")
        self.__master_contracts_by_token = {}
        self.__master_contracts_by_symbol = {}
        if(master_contracts_to_download == None):
            for e in self.__enabled_exchanges:
                self.__get_master_contract(e)
        else:
            for e in master_contracts_to_download:
                self.__get_master_contract(e)
        self.ws_thread = None

    @staticmethod
    def login_and_get_access_token(username, password, twoFA, api_secret, redirect_url='https://ant.aliceblueonline.com/plugin/callback', app_id=None):
        """ Login and get access token """
        #Get the Code
        if(app_id is None):
            app_id = username
        r = requests.Session()
        config = AliceBlue.__service_config
        url = f"{config['host']}{config['routes']['authorize']}?response_type=code&state=test_state&client_id={app_id}&redirect_uri={redirect_url}" 
        resp = r.get(url)
        if('OAuth 2.0 Error' in resp.text):
            logger.error("OAuth 2.0 Error occurred. Please verify your api_secret")
            return None
        page = BeautifulSoup(resp.text, features="html.parser")
        csrf_token = page.find('input', attrs = {'name':'_csrf_token'})['value']
        login_challenge = page.find('input', attrs = {'name' : 'login_challenge'})['value']
        resp = r.post(resp.url,data={'client_id':username,'password':password,'login_challenge':login_challenge,'_csrf_token':csrf_token})
        if('Please Enter Valid Password' in resp.text):
            logger.error("Please enter a valid password")
            return
        if('Internal server error' in resp.text):
            logger.error("Got Internal server error, please try again after sometimes")
            return
        question_ids = []
        page = BeautifulSoup(resp.text, features="html.parser")
        err = page.find('p', attrs={'class':'error'})
        if(len(err) > 0):
            logger.error(f"Couldn't login {err}")
            return
        for i in page.find_all('input', attrs={'name':'question_id1'}):
            question_ids.append(i['value'])
        logger.info(f"Assuming answers for all 2FA questions are '{twoFA}', Please change it to '{twoFA}' if not")
        resp = r.post(resp.url,data={'answer1':twoFA,'question_id1':question_ids,'answer2':twoFA,'login_challenge':login_challenge,'_csrf_token':csrf_token})
        if('consent_challenge' in resp.url):
            logger.info("Authorizing app for the first time")
            page = BeautifulSoup(resp.text, features="html.parser")
            csrf_token = page.find('input', attrs = {'name':'_csrf_token'})['value']
            resp = r.post(url=resp.url,data={'_csrf_token':csrf_token, 'consent': "Authorize", "scopes": ""})
            if('Internal server error' in resp.text):
                logger.error(f"Getting 'Internal server error' while authorizing the app for the first time. Please login manually using the following url '{url}'")
                return
        code = resp.url[resp.url.index('=')+1:resp.url.index('&')]

        #Get Access Token
        params = {'code': code, 'redirect_uri': redirect_url, 'grant_type': 'authorization_code', 'client_secret' : api_secret, "cliend_id": username}
        url = f"{config['host']}{config['routes']['access_token']}?client_id={app_id}&client_secret={api_secret}&grant_type=authorization_code&code={code}&redirect_uri={redirect_url}&authorization_response={resp.url}"
        resp = r.post(url,auth=(app_id, api_secret),data=params)
        resp = json.loads(resp.text)
        if('access_token' in resp):
            access_token = resp['access_token']
            logger.info(f'access_token - {access_token}')
            return access_token
        else:
            logger.error(f"Couldn't get access token {resp}")
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
        if('exchange' in dictionary):
            d = self.__exchange_codes
            dictionary['exchange'] = list(d.keys())[list(d.values()).index(dictionary['exchange'])]
        return dictionary

    def __convert_instrument(self, dictionary):
        if('exchange' in dictionary) and ('token' in dictionary):
            dictionary['instrument'] = self.get_instrument_by_token(dictionary['exchange'], dictionary['token'])
        return dictionary
        
    def __modify_human_readable_values(self, dictionary):
        dictionary = self.__convert_prices(dictionary, self.__exchange_price_multipliers[dictionary['exchange']])
        dictionary = self.__conver_exchanges(dictionary)
        dictionary = self.__convert_instrument(dictionary)
        return dictionary

    def __on_data_callback(self, ws=None, message=None, data_type=None, continue_flag=None):
        if(type(ws) is not websocket.WebSocketApp): # This workaround is to solve the websocket_client's compatiblity issue of older versions. ie.0.40.0 which is used in upstox. Now this will work in both 0.40.0 & newer version of websocket_client
            message = ws
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
            if(self.__dpr_callback is not None):
                self.__dpr_callback(res)
        elif(message[0] == WsFrameMode.OI):
            p = OpenInterest.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p) 
            if(self.__oi_callback is not None):
                self.__oi_callback(res)
        elif(message[0] == WsFrameMode.MARKET_STATUS):
            p = MarketStatus.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p)
            self.__market_status_messages.append(res) 
            if(self.__market_status_messages_callback is not None):
                self.__market_status_messages_callback(res)
        elif(message[0] == WsFrameMode.EXCHANGE_MESSAGES):
            p = ExchangeMessage.parse(message[1:]).__dict__
            res = self.__modify_human_readable_values(p)
            self.__exchange_messages.append(res) 
            if(self.__exchange_messages_callback is not None):
                self.__exchange_messages_callback(res)
         
    def __on_close_callback(self, ws=None):
        self.__websocket_connected = False
        if self.__on_disconnect:
            self.__on_disconnect()

    def __on_open_callback(self, ws=None):
        self.__websocket_connected = True
        self.__resubscribe()
        if self.__on_open:
            self.__on_open()

    def __on_error_callback(self, ws=None, error=None):
        if(type(ws) is not websocket.WebSocketApp): # This workaround is to solve the websocket_client's compatiblity issue of older versions. ie.0.40.0 which is used in upstox. Now this will work in both 0.40.0 & newer version of websocket_client
            error = ws
        if self.__on_error:
            self.__on_error(error)

    def __send_heartbeat(self):
        heart_beat = {"a": "h", "v": [], "m": ""}
        while True:
            sleep(5)
            self.__ws_send(json.dumps(heart_beat), opcode = websocket._abnf.ABNF.OPCODE_PING)

    def __ws_run_forever(self):
        while True:
            try:
                self.__websocket.run_forever()
            except Exception as e:
                logger.warning(f"websocket run forever ended in exception, {e}")
            sleep(0.1) # Sleep for 100ms between reconnection.

    def __ws_send(self, *args, **kwargs):
        while self.__websocket_connected == False:
            sleep(0.05)  # sleep for 50ms if websocket is not connected, wait for reconnection
        with self.__ws_mutex:
            ret = self.__websocket.send(*args, **kwargs)
        return ret

    def start_websocket(self, subscribe_callback = None, 
                                order_update_callback = None,
                                socket_open_callback = None,
                                socket_close_callback = None,
                                socket_error_callback = None,
                                run_in_background=False,
                                market_status_messages_callback = None,
                                exchange_messages_callback = None,
                                oi_callback = None,
                                dpr_callback = None):
        """ Start a websocket connection for getting live data """
        self.__on_open = socket_open_callback
        self.__on_disconnect = socket_close_callback
        self.__on_error = socket_error_callback
        self.__subscribe_callback = subscribe_callback
        self.__order_update_callback = order_update_callback
        self.__market_status_messages_callback = market_status_messages_callback
        self.__exchange_messages_callback = exchange_messages_callback
        self.__oi_callback = oi_callback
        self.__dpr_callback = dpr_callback
        
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
            self.__ws_thread = threading.Thread(target=self.__ws_run_forever)
            self.__ws_thread.daemon = True
            self.__ws_thread.start()
        else:
            self.__ws_run_forever()

    def get_profile(self):
        """ Get profile """
        profile = self.__api_call_helper('profile', Requests.GET, None, None)
        if(profile['status'] != 'error'):
            self.__enabled_exchanges = profile['data']['exchanges']
        return profile

    def get_balance(self):
        """ Get balance/margins """
        return self.__api_call_helper('balance', Requests.GET, None, None)

    def get_daywise_positions(self):
        """ Get daywise positions """
        return self.__api_call_helper('positions_daywise', Requests.GET, None, None)

    def get_netwise_positions(self):
        """ Get netwise positions """
        return self.__api_call_helper('positions_netwise', Requests.GET, None, None)

    def get_holding_positions(self):
        """ Get holding positions """
        return self.__api_call_helper('positions_holdings', Requests.GET, None, None)

    def get_order_history(self, order_id=None):
        """ leave order_id as None to get all entire order history """
        if order_id is None:
            return self.__api_call_helper('get_orders', Requests.GET, None, None);
        else:
            return self.__api_call_helper('get_order_info', Requests.GET, {'order_id': order_id}, None);
    
    def get_scrip_info(self, instrument):
        """ Get scrip information """
        params = {'exchange': instrument.exchange, 'token': instrument.token}
        return self.__api_call_helper('scripinfo', Requests.GET, params, None)

    def get_trade_book(self):
        """ get all trades """
        return self.__api_call_helper('trade_book', Requests.GET, None, None)

    def get_exchanges(self):
        """ Get enabled exchanges """
        return self.__enabled_exchanges

    def __get_product_type_str(self, product_type, exchange):
        prod_type = None
        if(product_type == ProductType.Intraday):
            prod_type = 'MIS'
        elif(product_type == ProductType.Delivery):
            if(exchange == 'NFO') or (exchange == 'MCX') or (exchange == 'CDS'):
                prod_type = 'NRML'
            else:
                prod_type = 'CNC'
        elif(product_type == ProductType.CoverOrder):
            prod_type = 'CO'
        elif(product_type == ProductType.BracketOrder):
            prod_type = None
        return prod_type

    def place_order(self, transaction_type, instrument, quantity, order_type,
                    product_type, price=0.0, trigger_price=None,
                    stop_loss=None, square_off=None, trailing_sl=None,
                    is_amo = False,
                    order_tag = 'order1'):
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

        prod_type = self.__get_product_type_str(product_type, instrument.exchange)
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
                   'product':prod_type,
                   'source':'web',
                   'order_tag': order_tag}

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

        if(is_amo == True):
            helper = 'place_amo'
        else:
            helper = 'place_order'

        if product_type is ProductType.BracketOrder:
            helper = 'place_bracket_order'
            del order['product'] 
            if not isinstance(stop_loss, float):
                raise TypeError("Required parameter stop_loss not of type float")

            if not isinstance(square_off, float):
                raise TypeError("Required parameter square_off not of type float")
            
        return self.__api_call_helper(helper, Requests.POST, None, order)

    def place_basket_order(self, orders):
        """ placing a basket order, 
            Argument orders should be a list of all orders that should be sent
            each element in order should be a dictionary containing the following key.
            "instrument", "order_type", "quantity", "price" (only if its a limit order), 
            "transaction_type", "product_type"
        """
        keys = {"instrument"        : Instrument, 
                "order_type"        : OrderType, 
                "quantity"          : int,
                "transaction_type"  : TransactionType,
                "product_type"      : ProductType}
        if not isinstance(orders, list):
            raise TypeError("Required parameter orders is not of type list")

        if len(orders) <= 0:
            raise TypeError("Length of orders should be greater than 0")

        for i in orders:
            if not isinstance(i, dict):
                raise TypeError("Each element in orders should be of type dict")
            for s in keys:
                if s not in i:
                    raise TypeError(f"Each element in orders should have key {s}")
                if type(i[s]) is not keys[s]:  
                    raise TypeError(f"Element '{s}' in orders should be of type {keys[s]}")
            if i['order_type'] == OrderType.Limit:
                if "price" not in i:
                    raise TypeError("Each element in orders should have key 'price' if its a limit order ")
                if not isinstance(i['price'], float):
                    raise TypeError("Element price in orders should be of type float")
            else:
                i['price'] = 0.0
            if i['order_type'] == OrderType.StopLossLimit or i['order_type'] == OrderType.StopLossMarket:
                if 'trigger_price' not in i:
                    raise TypeError(f"Each element in orders should have key 'trigger_price' if it is an {i['order_type']} order")
                if not isinstance(i['trigger_price'], float):
                    raise TypeError("Element trigger_price in orders should be of type float")
            else:
                i['trigger_price'] = 0.0
                
            if(i['product_type'] == ProductType.CoverOrder):
                raise TypeError("Product Type CO is not supported in basket order")
            elif(i['product_type'] == ProductType.BracketOrder):
                raise TypeError("Product Type BO is not supported in basket order")
            else:
                i['product_type'] = self.__get_product_type_str(i['product_type'], i['instrument'].exchange)
                
            if i['quantity'] <= 0:
                raise TypeError("Quantity should be greater than 0")

        data = {'source':'web',
                'orders' : []}
        for i in orders:
            # construct order object after all required parameters are met
            data['orders'].append({'exchange'           : i['instrument'].exchange,
                                   'order_type'         : i['order_type'].value,
                                   'instrument_token'   : i['instrument'].token,
                                   'quantity'           : i['quantity'],
                                   'disclosed_quantity' : 0,
                                   'price'              : i['price'],
                                   'transaction_type'   : i['transaction_type'].value,
                                   'trigger_price'      : i['trigger_price'],
                                   'validity'           : 'DAY',
                                   'product'            : i['product_type']})

        helper = 'place_basket_order'
        return self.__api_call_helper(helper, Requests.POST, None, data)

    def modify_order(self, transaction_type, instrument, product_type, order_id, order_type, quantity, price=0.0,
                     trigger_price=0.0):
        """ modify an order, transaction_type, instrument, product_type, order_id & order_type is required, 
            rest are optional, use only when when you want to change that attribute.
        """
        if not isinstance(instrument, Instrument):
            raise TypeError("Required parameter instrument not of type Instrument")

        if not isinstance(order_id, str):
            raise TypeError("Required parameter order_id not of type str")

        if not isinstance(quantity, int):
            raise TypeError("Optional parameter quantity not of type int")

        if type(order_type) is not OrderType:
            raise TypeError("Optional parameter order_type not of type OrderType")

        if ProductType is None:
            raise TypeError("Required parameter product_type not of type ProductType")

        if price is not None and not isinstance(price, float):
            raise TypeError("Optional parameter price not of type float")

        if trigger_price is not None and not isinstance(trigger_price, float):
            raise TypeError("Optional parameter trigger_price not of type float")

        product_type = self.__get_product_type_str(product_type, instrument.exchange)
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
                   'disclosed_quantity':0,
                   'nest_request_id' : '1'}
        return self.__api_call_helper('modify_order', Requests.PUT, None, order)

    def cancel_order(self, order_id, leg_order_id=None, is_co=False):
        """ Cancel single order """
        if(is_co == False):
            if(leg_order_id == None):
                ret = self.__api_call_helper('cancel_order', Requests.DELETE, {'order_id': order_id}, None)
            else:
                ret = self.__api_call_helper('cancel_bo_order', Requests.DELETE, {'order_id': order_id, 'leg_order_id': leg_order_id}, None)
        else:
            ret = self.__api_call_helper('cancel_co_order', Requests.DELETE, {'order_id': order_id, 'leg_order_id': leg_order_id}, None)
        return ret

    def cancel_all_orders(self):
        """ Cancel all orders """
        ret = []
        orders = self.get_order_history()['data']
        if not orders:
            return
        for c_order in orders['pending_orders']:
            if(c_order['product'] == 'BO' and c_order['leg_order_indicator']):
                r = self.cancel_order(c_order['leg_order_indicator'], leg_order_id = c_order['leg_order_indicator'])
            elif(c_order['product'] == 'CO'):
                r = self.cancel_order(c_order['oms_order_id'], leg_order_id = c_order['leg_order_indicator'], is_co = True)
            else:
                r = self.cancel_order(c_order['oms_order_id'])
            ret.append(r)
        return ret

    def subscribe_market_status_messages(self):
        """ Subscribe to market messages """
        return self.__ws_send(json.dumps({"a": "subscribe", "v": [1,2,3,4,6], "m": "market_status"}))

    def get_market_status_messages(self):
        """ Get market messages """
        return self.__market_status_messages
    
    def subscribe_exchange_messages(self):
        """ Subscribe to exchange messages """
        return self.__ws_send(json.dumps({"a": "subscribe", "v": [1,2,3,4,6], "m": "exchange_messages"}))

    def get_exchange_messages(self):
        """ Get stored exchange messages """
        return self.__exchange_messages
    
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
                arr.append([exchange, int(_instrument.token)])
                self.__subscribers[_instrument] = live_feed_type
        else:
            if not isinstance(instrument, Instrument):
                raise TypeError("Required parameter instrument not of type Instrument")
            exchange = self.__exchange_codes[instrument.exchange]
            arr = [[exchange, int(instrument.token)]]
            self.__subscribers[instrument] = live_feed_type
        if(live_feed_type == LiveFeedType.MARKET_DATA):
            mode = 'marketdata' 
        elif(live_feed_type == LiveFeedType.COMPACT):
            mode = 'compact_marketdata' 
        elif(live_feed_type == LiveFeedType.SNAPQUOTE):
            mode = 'snapquote' 
        elif(live_feed_type == LiveFeedType.FULL_SNAPQUOTE):
            mode = 'full_snapquote' 
        data = json.dumps({'a' : 'subscribe', 'v' : arr, 'm' : mode})
        return self.__ws_send(data)

    def unsubscribe(self, instrument, live_feed_type):
        """ unsubscribe to the current feed of an instrument """
        if(type(live_feed_type) is not LiveFeedType):
            raise TypeError("Required parameter live_feed_type not of type LiveFeedType")
        arr = []
        if (isinstance(instrument, list)):
            for _instrument in instrument:
                if not isinstance(_instrument, Instrument):
                    raise TypeError("Required parameter instrument not of type Instrument")
                exchange = self.__exchange_codes[_instrument.exchange] 
                arr.append([exchange, int(_instrument.token)])
                if(_instrument in self.__subscribers): del self.__subscribers[_instrument]
        else:
            if not isinstance(instrument, Instrument):
                raise TypeError("Required parameter instrument not of type Instrument")
            exchange = self.__exchange_codes[instrument.exchange]
            arr = [[exchange, int(instrument.token)]]
            if(instrument in self.__subscribers): del self.__subscribers[instrument]
        if(live_feed_type == LiveFeedType.MARKET_DATA):
            mode = 'marketdata' 
        elif(live_feed_type == LiveFeedType.COMPACT):
            mode = 'compact_marketdata' 
        elif(live_feed_type == LiveFeedType.SNAPQUOTE):
            mode = 'snapquote' 
        elif(live_feed_type == LiveFeedType.FULL_SNAPQUOTE):
            mode = 'full_snapquote' 
        data = json.dumps({'a' : 'unsubscribe', 'v' : arr, 'm' : mode})
        return self.__ws_send(data)

    def get_all_subscriptions(self):
        """ get the all subscribed instruments """
        return self.__subscribers
    
    def __resubscribe(self):
        market = []
        compact = []
        snap = []
        full = []
        for key, value in self.get_all_subscriptions().items():
            if(value == LiveFeedType.MARKET_DATA):
                market.append(key) 
            elif(value == LiveFeedType.COMPACT):
                compact.append(key) 
            elif(value == LiveFeedType.SNAPQUOTE):
                snap.append(key) 
            elif(value == LiveFeedType.FULL_SNAPQUOTE):
                full.append(key)
        if(len(market) > 0):
            self.subscribe(market, LiveFeedType.MARKET_DATA)
        if(len(compact) > 0):
            self.subscribe(compact, LiveFeedType.COMPACT)
        if(len(snap) > 0):
            self.subscribe(snap, LiveFeedType.SNAPQUOTE)
        if(len(full) > 0):
            self.subscribe(full, LiveFeedType.FULL_SNAPQUOTE)

    def get_instrument_by_symbol(self, exchange, symbol):
        """ get instrument by providing symbol """
        # get instrument given exchange and symbol
        exchange = exchange.upper()
        # check if master contract exists
        if exchange not in self.__master_contracts_by_symbol:
            logger.warning(f"Cannot find exchange {exchange} in master contract. "
                            "Please ensure if that exchange is enabled in your profile and downloaded the master contract for the same")
            return None
        master_contract = self.__master_contracts_by_symbol[exchange]
        if symbol not in master_contract:
            logger.warning(f"Cannot find symbol {exchange} {symbol} in master contract")
            return None
        return master_contract[symbol]
    
    def get_instrument_for_fno(self, symbol, expiry_date, is_fut=False, strike=None, is_CE = False, exchange = 'NFO'):
        """ get instrument for FNO """
        res = self.search_instruments(exchange, symbol)
        if(res == None):
            return
        matches = []
        for i in res:
            sp = i.symbol.split(' ')
            if(sp[0] == symbol):
                if(i.expiry == expiry_date):
                    matches.append(i)
        for i in matches:
            if(is_fut == True):
                if('FUT' in i.symbol):
                    return i
            else:
                sp = i.symbol.split(' ')
                if((sp[-1] == 'CE') or (sp[-1] == 'PE')):           # Only option scrips 
                    if(float(sp[-2]) == float(strike)):
                        if(is_CE == True):
                            if(sp[-1] == 'CE'):
                                return i
                        else:
                            if(sp[-1] == 'PE'):
                                return i
                            
    def search_instruments(self, exchange, symbol):
        """ Search instrument by symbol match """
        # search instrument given exchange and symbol
        exchange = exchange.upper()
        matches = []
        # check if master contract exists
        if exchange not in self.__master_contracts_by_token:
            logger.warning(f"Cannot find exchange {exchange} in master contract. "
                "Please ensure if that exchange is enabled in your profile and downloaded the master contract for the same")
            return None
        master_contract = self.__master_contracts_by_token[exchange]
        for contract in master_contract:
            if (isinstance(symbol, list)):
                for sym in symbol:
                    if sym.lower() in master_contract[contract].symbol.split(' ')[0].lower():
                        matches.append(master_contract[contract])
            else:
                if symbol.lower() in master_contract[contract].symbol.split(' ')[0].lower():
                    matches.append(master_contract[contract])
        return matches

    def get_instrument_by_token(self, exchange, token):
        """ Get instrument by providing token """
        # get instrument given exchange and token
        exchange = exchange.upper()
        token = int(token)
        # check if master contract exists
        if exchange not in self.__master_contracts_by_symbol:
            logger.warning(f"Cannot find exchange {exchange} in master contract. "
                            "Please ensure if that exchange is enabled in your profile and downloaded the master contract for the same")
            return None
        master_contract = self.__master_contracts_by_token[exchange]
        if token not in master_contract:
            logger.warning(f"Cannot find symbol {exchange} {token} in master contract")
            return None
        return master_contract[token]

    def get_master_contract(self, exchange):
        """ Get master contract """
        return self.__master_contracts_by_symbol[exchange]

    def __get_master_contract(self, exchange):
        """ returns all the tradable contracts of an exchange
            placed in an OrderedDict and the key is the token
        """
        logger.info(f'Downloading master contracts for exchange: {exchange}')
        body = self.__api_call_helper('master_contract', Requests.GET, {'exchange': exchange}, None)
        master_contract_by_token = OrderedDict()
        master_contract_by_symbol = OrderedDict()
        for sub in body:
            for scrip in body[sub]:
                # convert token
                token = int(scrip['code'])
    
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
        #logger.debug('url:: %s http_method:: %s data:: %s headers:: %s', url, http_method, data, headers)
        headers = {"Content-Type": "application/json"} 
        if(len(self.__access_token) > 100):
            headers['X-Authorization-Token'] = self.__access_token
            headers['Connection'] = 'keep-alive'
        else:
            headers['client_id'] = self.__username
            headers['authorization'] = f"Bearer {self.__access_token}"
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
