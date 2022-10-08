from collections import namedtuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from time import sleep
from urllib.parse import urlparse, parse_qs
import base64
import datetime
import enum
import hashlib
import json
import logging
import os
import pytz
import requests
import tempfile
import threading
import websocket

Instrument = namedtuple('Instrument', ['exchange', 'token', 'symbol',
                                       'name', 'expiry', 'lot_size'])
logger = logging.getLogger(__name__)

class Requests(enum.IntEnum):
    PUT     = 1
    DELETE  = 2
    GET     = 3
    POST    = 4

class TransactionType(enum.Enum):
    Buy = 'BUY'
    Sell = 'SELL'

class OrderType(enum.Enum):
    Market = 'MKT'
    Limit = 'L'
    StopLossLimit = 'SL'
    StopLossMarket = 'SL-M'
    BracketOrder = "BO"
    AfterMarketOrder = "AMO"

class ProductType(enum.Enum):
    Intraday = 0
    Delivery = 1

class LiveFeedType(enum.IntEnum):
    TICK_DATA     = 1
    DEPTH_DATA      = 2

class HistoricalDataType(enum.Enum):
    Day = '1D'
    Minute = '1'

class CryptoJsAES:
    @staticmethod
    def __pad(data):
        BLOCK_SIZE = 16
        length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
        return data + (chr(length)*length).encode()

    @staticmethod
    def __unpad(data):
        return data[:-(data[-1] if type(data[-1]) == int else ord(data[-1]))]

    @staticmethod
    def __bytes_to_key(data, salt, output=48):
        assert len(salt) == 8, len(salt)
        data += salt
        key = hashlib.md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = hashlib.md5(key + data).digest()
            final_key += key
        return final_key[:output]

    @staticmethod
    def encrypt(message, passphrase):
        salt = os.urandom(8)
        key_iv = CryptoJsAES.__bytes_to_key(passphrase, salt, 32+16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = Cipher(algorithms.AES(key), modes.CBC(iv))
        return base64.b64encode(b"Salted__" + salt + aes.encryptor().update(CryptoJsAES.__pad(message)) + aes.encryptor().finalize())

    @staticmethod
    def decrypt(encrypted, passphrase):
        encrypted = base64.b64decode(encrypted)
        assert encrypted[0:8] == b"Salted__"
        salt = encrypted[8:16]
        key_iv = CryptoJsAES.__bytes_to_key(passphrase, salt, 32+16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = Cipher(algorithms.AES(key), modes.CBC(iv))
        return CryptoJsAES.__unpad(aes.decryptor.update(encrypted[16:]) + aes.decryptor().finalize())

class AliceBlue:
    """ AliceBlue Class for all operations related to AliceBlue Server"""

    # URLs
    host = "https://a3.aliceblueonline.com/rest/AliceBlueAPIService"
    __urls = {  "webLogin"              :   f"{host}/customer/webLogin",
                "twoFA"                 :   f"{host}/sso/validAnswer",
                "sessionID"             :   f"{host}/sso/getUserDetails",
                "getEncKey"             :   f"{host}/customer/getEncryptionKey",
                "authorizeVendor"       :   f"{host}/sso/authorizeVendor",
                "apiGetEncKey"          :   f"{host}/api/customer/getAPIEncpkey",
                "profile"               :   f"{host}/api/customer/accountDetails",
                "placeOrder"            :   f"{host}/api/placeOrder/executePlaceOrder",
                "logout"                :   f"{host}/api/customer/logout",
                "logoutFromAllDevices"  :   f"{host}/api/customer/logOutFromAllDevice",
                "fetchMWList"           :   f"{host}/api/marketWatch/fetchMWList",
                "fetchMWScrips"         :   f"{host}/api/marketWatch/fetchMWScrips",
                "addScripToMW"          :   f"{host}/api/marketWatch/addScripToMW",
                "deleteMWScrip"         :   f"{host}/api/marketWatch/deleteMWScrip",
                "scripDetails"          :   f"{host}/api/ScripDetails/getScripQuoteDetails",
                "positions"             :   f"{host}/api/positionAndHoldings/positionBook",
                "holdings"              :   f"{host}/api/positionAndHoldings/holdings",
                "sqrOfPosition"         :   f"{host}/api/positionAndHoldings/sqrOofPosition",
                "fetchOrder"            :   f"{host}/api/placeOrder/fetchOrderBook",
                "fetchTrade"            :   f"{host}/api/placeOrder/fetchTradeBook",
                "exitBracketOrder"      :   f"{host}/api/placeOrder/exitBracketOrder",
                "modifyOrder"           :   f"{host}/api/placeOrder/modifyOrder",
                "cancelOrder"           :   f"{host}/api/placeOrder/cancelOrder",
                "orderHistory"          :   f"{host}/api/placeOrder/orderHistory",
                "getRmsLimits"          :   f"{host}/api/limits/getRmsLimits",
                "createWsSession"       :   f"{host}/api/ws/createSocketSess",
                "history"               :   f"{host}/api/chart/history",
                "master_contract"       :   "https://v2api.aliceblueonline.com/restpy/contract_master?exch={exchange}",
                "ws"                    :   "wss://ws2.aliceblueonline.com/NorenWS/"
            }

    def __init__(self, username, session_id, master_contracts_to_download = None):
        """ Create Alice Blue object, get enabled exchanges and products for user """
        self.__username = username
        self.__session_id = session_id
        self.__websocket = None
        self.__websocket_connected = False
        self.__ws_mutex = threading.Lock()
        self.__on_error = None
        self.__on_disconnect = None
        self.__on_open = None
        self.__subscribe_callback = None
        self.__order_tag = 1
        self.__order_update_callback = None
        self.__market_status_messages_callback = None
        self.__exchange_messages_callback = None
        self.__subscribers = {}
        self.__market_status_messages = []
        self.__exchange_messages = []
        # Initialize Depth data
        self.__depth_data = {} 
        self.__tick_data = {} 

        try:
            self.get_profile()
        except Exception as e:
            raise Exception(f"Couldn't get profile info with credentials provided '{e}'")
        self.__master_contracts_by_token = {}
        self.__master_contracts_by_symbol = {}
        self.__get_master_contract("INDICES")
        if(master_contracts_to_download == None):
            for e in self.__enabled_exchanges:
                self.__get_master_contract(e)
        else:
            for e in master_contracts_to_download:
                self.__get_master_contract(e)
        self.ws_thread = None

    @staticmethod
    def login_and_get_sessionID(username, password, twoFA, app_id, api_secret):
        """ Login and get Session ID """
        header = {"Content-Type" : "application/json"}
        try:
            dr = tempfile.gettempdir()
            tmp_file = os.path.join(dr, f"alice_blue_key_{username}.json")
            if(os.path.isfile(tmp_file) == True):
                d = {}
                with open(tmp_file, 'r') as fo:
                    d = json.loads(fo.read())
                if(len(d["session_id"])):
                    # Try getting profile/account details
                    data = {"userId" : username}
                    hdr = { "Content-Type" : "application/json",
                            "Authorization" : f"Bearer {username} {d['session_id']}"}
                    r = requests.get(AliceBlue.__urls["profile"], headers=hdr, data=json.dumps(data))
                    logging.info(f"Get Account details response {r.text}")
                    if(r.status_code == 200):
                        if("stat" not in r.json()):
                            logging.info(f"Using stored session_id {d['session_id']}")
                            return d['session_id']
            with open(tmp_file, 'w') as fo:
                d = {"session_id" : ""}
                fo.write(json.dumps(d))
        except Exception as e:
            logging.warn(f"Getting session_id from temp file ended in exception {e}")
        # Get Encryption Key
        data = {"userId" : username}
        r = requests.post(AliceBlue.__urls['getEncKey'], headers=header, json=data)
        logging.info(f"Get Encryption Key response {r.text}")
        encKey = r.json()["encKey"]

        # Web Login
        checksum = CryptoJsAES.encrypt(password.encode(), encKey.encode())
        checksum = checksum.decode("utf-8")
        data = {"userId" : username,
                "userData" : checksum}
        r = requests.post(AliceBlue.__urls["webLogin"], json=data)
        logging.info(f"Web Login response {r.text}")

        # Web Login 2FA
        data = {"answer1" : twoFA,
                "sCount" : "1",
                "sIndex" : "1",
                "userId" : username,
                "vendor" : app_id}
        r = requests.post(AliceBlue.__urls["twoFA"], json=data)
        logging.info(f"Web Login 2FA response {r.text}")
        isAuthorized = r.json()['isAuthorized']
        authCode = parse_qs(urlparse(r.json()["redirectUrl"]).query)['authCode'][0]
        logging.info(f"isAuthorized {isAuthorized}")
        logging.info(f"authCode {authCode}")

        # Get API Encryption Key
        data = {"userId" : username}
        r = requests.post(AliceBlue.__urls["apiGetEncKey"], headers=header, data=json.dumps(data))
        logging.info(f"Get API Encryption Key response {r.text}")

        # Get User Details/Session ID
        checksum = hashlib.sha256(f"{username}{authCode}{api_secret}".encode()).hexdigest()
        data = {"checkSum" : checksum}
        r = requests.post(AliceBlue.__urls["sessionID"], headers=header, data=json.dumps(data))
        logging.info(f"Session ID response {r.text}")
        session_id = r.json()['userSession']
        logging.info(f"Session ID is {session_id}")

        # Authorize vendor app
        if(isAuthorized == False):
            data = {"userId" : username,
                    "vendor" : app_id}
            print("Authorizing vendor app")
            r = requests.post(AliceBlue.__urls["authorizeVendor"], headers=header, data=json.dumps(data))

        # Write session_id in temp file for next time usage
        with open(tmp_file, 'w') as fo:
            d = {"session_id" : session_id}
            fo.write(json.dumps(d))
        return session_id

    def __extract_tick_data(self, data):
        if("tk" in data):               # Token
            data["instrument"] = self.get_instrument_by_token(data.pop("e"), int(data.pop("tk")))
        if("ts" in data):               # Symbol
            data.pop("ts")
        if(data["instrument"].symbol not in self.__tick_data):
            self.__tick_data[data["instrument"].symbol] = {}
            self.__tick_data[data["instrument"].symbol]["ltp"] = 0
            self.__tick_data[data["instrument"].symbol]["percent_change"] = 0
            self.__tick_data[data["instrument"].symbol]["change_value"] = 0
            self.__tick_data[data["instrument"].symbol]["volume"] = 0
            self.__tick_data[data["instrument"].symbol]["open"] = 0
            self.__tick_data[data["instrument"].symbol]["high"] = 0
            self.__tick_data[data["instrument"].symbol]["low"] = 0
            self.__tick_data[data["instrument"].symbol]["close"] = 0
            self.__tick_data[data["instrument"].symbol]["exchange_time_stamp"] = None
            self.__tick_data[data["instrument"].symbol]["atp"] = 0
            self.__tick_data[data["instrument"].symbol]["tick_increment"] = 0
            self.__tick_data[data["instrument"].symbol]["lot_size"] = 0
            self.__tick_data[data["instrument"].symbol]["price_precision"] = 0
            self.__tick_data[data["instrument"].symbol]["total_open_interest"] = 0
        if("lp" in data):               # Last Traded Price
            self.__tick_data[data["instrument"].symbol]["ltp"] = float(data.pop("lp"))
        if("pc" in data):               # percentage change
            self.__tick_data[data["instrument"].symbol]["percent_change"] = float(data.pop("pc"))
        if("cv" in data):               # change value (absolute change in price)
            self.__tick_data[data["instrument"].symbol]["change_value"] = float(data.pop("cv"))
        if("v" in data):                # Volume
            self.__tick_data[data["instrument"].symbol]["volume"] = int(data.pop("v"))
        if("o" in data):                # Open
            self.__tick_data[data["instrument"].symbol]["open"] = float(data.pop("o"))
        if("h" in data):                # High
            self.__tick_data[data["instrument"].symbol]["high"] = float(data.pop("h"))
        if("l" in data):                # Low
            self.__tick_data[data["instrument"].symbol]["low"] = float(data.pop("l"))
        if("c" in data):                # Close
            self.__tick_data[data["instrument"].symbol]["close"] = float(data.pop("c"))
        if("ft" in data):               # Feed Time
            self.__tick_data[data["instrument"].symbol]["exchange_time_stamp"] = datetime.datetime.fromtimestamp(int(data.pop("ft")))
        if("ap" in data):               # Average Price
            self.__tick_data[data["instrument"].symbol]["atp"] = float(data.pop("ap"))
        if("ti" in data):               # Tick Increment
            self.__tick_data[data["instrument"].symbol]["tick_increment"] = float(data.pop("ti"))
        if("ls" in data):               # Lot Size
            self.__tick_data[data["instrument"].symbol]["lot_size"] = int(data.pop("ls"))
        if(data["instrument"].symbol not in self.__depth_data):                # Initialize depth data
            self.__depth_data[data["instrument"].symbol] = {}
            self.__depth_data[data["instrument"].symbol]["bid_prices"]          = [None, None, None, None, None]
            self.__depth_data[data["instrument"].symbol]["ask_prices"]          = [None, None, None, None, None]
            self.__depth_data[data["instrument"].symbol]["bid_quantities"]      = [None, None, None, None, None]
            self.__depth_data[data["instrument"].symbol]["ask_quantities"]      = [None, None, None, None, None]
            self.__depth_data[data["instrument"].symbol]["buy_orders"]          = [None, None, None, None, None]
            self.__depth_data[data["instrument"].symbol]["sell_orders"]         = [None, None, None, None, None]
            self.__depth_data[data["instrument"].symbol]["open_interest"]       = 0
            self.__depth_data[data["instrument"].symbol]["last_traded_quantity"]= 0
            self.__depth_data[data["instrument"].symbol]["last_traded_time"]    = None
            self.__depth_data[data["instrument"].symbol]["total_buy_quantity"]  = 0
            self.__depth_data[data["instrument"].symbol]["total_sell_quantity"] = 0
            self.__depth_data[data["instrument"].symbol]["upper_circuit"]       = 0
            self.__depth_data[data["instrument"].symbol]["lower_circuit"]       = 0

        if("bp1" in data):               # Best Bid
            self.__depth_data[data["instrument"].symbol]["bid_prices"][0] = float(data.pop("bp1"))
        if("sp1" in data):               # Best Ask
            self.__depth_data[data["instrument"].symbol]["ask_prices"][0] = float(data.pop("sp1"))
        if("bq1" in data):               # Best Bid Quantity
            self.__depth_data[data["instrument"].symbol]["bid_quantities"][0] = int(data.pop("bq1"))
        if("sq1" in data):               # Best Ask Quantity
            self.__depth_data[data["instrument"].symbol]["ask_quantities"][0] = int(data.pop("sq1"))
        if("pp" in data):                # Price Precision
            self.__tick_data[data["instrument"].symbol]["price_precision"] = int(data.pop("pp"))
        if("toi" in data):               # Total Open Interest
            self.__tick_data[data["instrument"].symbol]["total_open_interest"] = int(data.pop("toi"))
        data["ltp"]                 = self.__tick_data[data["instrument"].symbol]["ltp"]
        data["percent_change"]      = self.__tick_data[data["instrument"].symbol]["percent_change"]
        data["change_value"]        = self.__tick_data[data["instrument"].symbol]["change_value"]
        data["volume"]              = self.__tick_data[data["instrument"].symbol]["volume"]
        data["open"]                = self.__tick_data[data["instrument"].symbol]["open"]
        data["high"]                = self.__tick_data[data["instrument"].symbol]["high"]
        data["low"]                 = self.__tick_data[data["instrument"].symbol]["low"]
        data["close"]               = self.__tick_data[data["instrument"].symbol]["close"]
        data["exchange_time_stamp"] = self.__tick_data[data["instrument"].symbol]["exchange_time_stamp"]
        data["atp"]                 = self.__tick_data[data["instrument"].symbol]["atp"]
        data["tick_increment"]      = self.__tick_data[data["instrument"].symbol]["tick_increment"]
        data["lot_size"]            = self.__tick_data[data["instrument"].symbol]["lot_size"]
        data["best_bid_price"]      = self.__depth_data[data["instrument"].symbol]["bid_prices"][0]
        data["best_ask_price"]      = self.__depth_data[data["instrument"].symbol]["ask_prices"][0]
        data["best_bid_quantity"]   = self.__depth_data[data["instrument"].symbol]["bid_quantities"][0]
        data["best_ask_quantity"]   = self.__depth_data[data["instrument"].symbol]["ask_quantities"][0]
        data["price_precision"]     = self.__tick_data[data["instrument"].symbol]["price_precision"]
        data["total_open_interest"] = self.__tick_data[data["instrument"].symbol]["total_open_interest"]
        return data
    
    def __extract_depth_data(self, data):
        """ example depth frame 
        message - {"t":"dk","pp":"2","ml":"1","e":"NSE","tk":"1594","ts":"INFY-EQ","ls":"1","ti":"0.05","c":"1461.75","lp":"1489.90","pc":"1.93","o":"1473.10","h":"1496.10","l":"1466.00","uc":"1607.90","lc":"1315.60","toi":"53068800","ft":"1661853600","ltq":"10","ltt":"15:29:59","v":"6724948","tbq":"308293","tsq":"177491","bp1":"1489.55","sp1":"1489.90","bp2":"1489.45","sp2":"1489.95","bp3":"1489.40","sp3":"1490.00","bp4":"1489.10","sp4":"1490.80","bp5":"1489.00","sp5":"1491.00","bq1":"1","sq1":"25","bq2":"5","sq2":"1358","bq3":"468","sq3":"2221","bq4":"500","sq4":"600","bq5":"30","sq5":"258","bo1":"1","so1":"1","bo2":"1","so2":"2","bo3":"2","so3":"5","bo4":"1","so4":"1","bo5":"3","so5":"6","ap":"1485.71"}"""
        # Extract tick data first
        data = self.__extract_tick_data(data)

        # Bid Prices
        if("bp2" in data):
            self.__depth_data[data["instrument"].symbol]["bid_prices"][1] = float(data.pop("bp2"))
        if("bp3" in data):
            self.__depth_data[data["instrument"].symbol]["bid_prices"][2] = float(data.pop("bp3"))
        if("bp4" in data):
            self.__depth_data[data["instrument"].symbol]["bid_prices"][3] = float(data.pop("bp4"))
        if("bp5" in data):
            self.__depth_data[data["instrument"].symbol]["bid_prices"][4] = float(data.pop("bp5"))

        # Ask Prices
        if("sp2" in data):
            self.__depth_data[data["instrument"].symbol]["ask_prices"][1] = float(data.pop("sp2"))
        if("sp3" in data):
            self.__depth_data[data["instrument"].symbol]["ask_prices"][2] = float(data.pop("sp3"))
        if("sp4" in data):
            self.__depth_data[data["instrument"].symbol]["ask_prices"][3] = float(data.pop("sp4"))
        if("sp5" in data):
            self.__depth_data[data["instrument"].symbol]["ask_prices"][4] = float(data.pop("sp5"))

        # Bid Quantities
        if("bq2" in data):
            self.__depth_data[data["instrument"].symbol]["bid_quantities"][1] = int(data.pop("bq2"))
        if("bq3" in data):
            self.__depth_data[data["instrument"].symbol]["bid_quantities"][2] = int(data.pop("bq3"))
        if("bq4" in data):
            self.__depth_data[data["instrument"].symbol]["bid_quantities"][3] = int(data.pop("bq4"))
        if("bq5" in data):
            self.__depth_data[data["instrument"].symbol]["bid_quantities"][4] = int(data.pop("bq5"))

        # Ask Quantities
        if("sq2" in data):
            self.__depth_data[data["instrument"].symbol]["ask_quantities"][1] = int(data.pop("sq2"))
        if("sq3" in data):
            self.__depth_data[data["instrument"].symbol]["ask_quantities"][2] = int(data.pop("sq3"))
        if("sq4" in data):
            self.__depth_data[data["instrument"].symbol]["ask_quantities"][3] = int(data.pop("sq4"))
        if("sq5" in data):
            self.__depth_data[data["instrument"].symbol]["ask_quantities"][4] = int(data.pop("sq5"))

        # Buy Orders
        if("bo1" in data):
            self.__depth_data[data["instrument"].symbol]["buy_orders"][1] = int(data.pop("bo1"))
        if("bo2" in data):
            self.__depth_data[data["instrument"].symbol]["buy_orders"][1] = int(data.pop("bo2"))
        if("bo3" in data):
            self.__depth_data[data["instrument"].symbol]["buy_orders"][2] = int(data.pop("bo3"))
        if("bo4" in data):
            self.__depth_data[data["instrument"].symbol]["buy_orders"][3] = int(data.pop("bo4"))
        if("bo5" in data):
            self.__depth_data[data["instrument"].symbol]["buy_orders"][4] = int(data.pop("bo5"))

        # Sell Orders
        if("so1" in data):
            self.__depth_data[data["instrument"].symbol]["sell_orders"][1] = int(data.pop("so1"))
        if("so2" in data):
            self.__depth_data[data["instrument"].symbol]["sell_orders"][1] = int(data.pop("so2"))
        if("so3" in data):
            self.__depth_data[data["instrument"].symbol]["sell_orders"][2] = int(data.pop("so3"))
        if("so4" in data):
            self.__depth_data[data["instrument"].symbol]["sell_orders"][3] = int(data.pop("so4"))
        if("so5" in data):
            self.__depth_data[data["instrument"].symbol]["sell_orders"][4] = int(data.pop("so5"))

        # Update depth data in dict
        data["bid_prices"] = self.__depth_data[data["instrument"].symbol]["bid_prices"].copy()
        data["ask_prices"] = self.__depth_data[data["instrument"].symbol]["ask_prices"].copy()
        data["bid_quantities"] = self.__depth_data[data["instrument"].symbol]["bid_quantities"].copy()
        data["ask_quantities"] = self.__depth_data[data["instrument"].symbol]["ask_quantities"].copy()
        data["buy_orders"] = self.__depth_data[data["instrument"].symbol]["buy_orders"].copy()
        data["sell_orders"] = self.__depth_data[data["instrument"].symbol]["sell_orders"].copy()

        if("oi" in data):               # Open Interest
            self.__depth_data[data["instrument"].symbol]["open_interest"] = int(data.pop("oi"))
        if("ltq" in data):               # Last Traded Quantity
            self.__depth_data[data["instrument"].symbol]["last_traded_quantity"] = int(data.pop("ltq"))
        if("ltt" in data):               # Last Traded Time
            self.__depth_data[data["instrument"].symbol]["last_traded_time"] = datetime.datetime.strptime(data.pop("ltt"), "%H:%M:%S").time()
        if("tbq" in data):               # Total Buy Quantity
            self.__depth_data[data["instrument"].symbol]["total_buy_quantity"] = int(data.pop("tbq"))
        if("tsq" in data):               # Total Sell Quantity
            self.__depth_data[data["instrument"].symbol]["total_sell_quantity"] = int(data.pop("tsq"))
        if("uc" in data):               # Upper Circuit
            self.__depth_data[data["instrument"].symbol]["upper_circuit"] = float(data.pop("uc"))
        if("lc" in data):               # Lower Circuit
            self.__depth_data[data["instrument"].symbol]["lower_circuit"] = float(data.pop("lc"))

        data["open_interest"]           = self.__depth_data[data["instrument"].symbol]["open_interest"]
        data["last_traded_quantity"]    = self.__depth_data[data["instrument"].symbol]["last_traded_quantity"]
        data["last_traded_time"]        = self.__depth_data[data["instrument"].symbol]["last_traded_time"] 
        data["total_buy_quantity"]      = self.__depth_data[data["instrument"].symbol]["total_buy_quantity"]
        data["total_sell_quantity"]     = self.__depth_data[data["instrument"].symbol]["total_sell_quantity"]
        data["upper_circuit"]           = self.__depth_data[data["instrument"].symbol]["upper_circuit"]
        data["lower_circuit"]           = self.__depth_data[data["instrument"].symbol]["lower_circuit"]
        return data

    def __on_data_callback(self, ws=None, message=None, data_type=None, continue_flag=None):
        # Sample messages 
        # message = '{"t":"tk","pp":"2","ml":"1","e":"NSE","tk":"1594","ts":"INFY-EQ","ls":"1","ti":"0.05","c":"1492.95","lp":"1464.55","pc":"-1.90","o":"1460.05","h":"1468.10","l":"1451.05","toi":"59451300","ft":"1662025323","v":"7397051","bp1":"1464.50","sp1":"1464.90","bq1":"22","sq1":"285","ap":"1460.13"}'
        # message = '{"t":"dk","pp":"2","ml":"1","e":"NSE","tk":"1594","ts":"INFY-EQ","ls":"1","ti":"0.05","c":"1492.95","lp":"1464.55","pc":"-1.90","o":"1460.05","h":"1468.10","l":"1451.05","uc":"1642.20","lc":"1343.70","toi":"59451300","ft":"1662025323","ltq":"47","ltt":"15:12:02","v":"7397051","tbq":"512544","tsq":"2368667","bp1":"1464.50","sp1":"1464.90","bp2":"1464.35","sp2":"1464.95","bp3":"1464.25","sp3":"1465.00","bp4":"1464.20","sp4":"1465.05","bp5":"1464.15","sp5":"1465.10","bq1":"22","sq1":"285","bq2":"88","sq2":"299","bq3":"460","sq3":"4173","bq4":"50","sq4":"300","bq5":"317","sq5":"242","bo1":"1","so1":"4","bo2":"1","so2":"6","bo3":"1","so3":"43","bo4":"1","so4":"1","bo5":"2","so5":"2","ap":"1460.13"}'
        # message = '{"t":"tf","e":"NSE","tk":"1594","ft":"1662025326","v":"7399482","bp1":"1464.25","sp1":"1464.35","bq1":"460","sq1":"11"}'
        # message = '{"t":"df","e":"NSE","tk":"1594","ft":"1662025327","v":"7400196","ltt":"15:12:07","tbq":"510593","tsq":"2364472","bp1":"1464.55","sp1":"1464.90","bp2":"1464.30","sp2":"1464.95","bp3":"1464.25","sp3":"1465.00","bp4":"1464.20","sp4":"1465.05","bp5":"1464.15","sp5":"1465.10","bq1":"1","sq1":"301","bq2":"598","sq2":"61","bq3":"83","sq3":"3573","bq4":"175","sq4":"300","bq5":"482","sq5":"51","bo2":"5","so2":"4","bo3":"2","so3":"42","bo4":"3","so4":"1","bo5":"5","so5":"2"}'
        # message = '{"t":"df","e":"NSE","tk":"1594","ft":"1662025324","v":"7397757","ltq":"2","ltt":"15:12:04","tbq":"513958","tsq":"2373240","sp1":"1464.95","sp2":"1465.00","sp3":"1465.05","sp4":"1465.10","sp5":"1465.15","bq1":"275","sq1":"37","sq2":"3472","sq3":"300","sq4":"26","sq5":"110","bo1":"5","so1":"8","so2":"40","so3":"1","so4":"2","so5":"4"}'
        # logging.info(f"message - {message}")
        if(type(ws) is not websocket.WebSocketApp): # This workaround is to solve the websocket_client's compatiblity issue of older versions. ie.0.40.0 which is used in upstox. Now this will work in both 0.40.0 & newer version of websocket_client
            message = ws
        data = json.loads(message)
        if(data["t"] == "ck"):           # Connection acknowledgment
            pass                            # Ignore Connection acknowledgment, nothing to extract from it
        elif(data["t"] == "tk"):         # tick data acknowledgment
            if(self.__subscribe_callback is not None):
                data.pop("t")
                data = self.__extract_tick_data(data)
                self.__subscribe_callback(data)
        elif(data["t"] == "dk"):         # depth data acknowledgment
            if(self.__subscribe_callback is not None):
                data.pop("t")
                data = self.__extract_depth_data(data)
                self.__subscribe_callback(data)
        elif(data["t"] == "tf"):         # tick data feed
            if(self.__subscribe_callback is not None):
                data.pop("t")
                data = self.__extract_tick_data(data)
                self.__subscribe_callback(data)
        elif(data["t"] == "df"):         # depth data feed
            if(self.__subscribe_callback is not None):
                data.pop("t")
                data = self.__extract_depth_data(data)
                self.__subscribe_callback(data)
         
    def __on_close_callback(self, *arguments, **keywords):
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

    def __ws_run_forever(self):
        while True:
            try:
                self.__websocket.run_forever(ping_interval=3, ping_payload='{"t":"h"}')
            except Exception as e:
                logger.warning(f"websocket run forever ended in exception, {e}")
            sleep(0.1) # Sleep for 100ms between reconnection.

    def __ws_send(self, data):
        while self.__websocket_connected == False:
            sleep(0.05)  # sleep for 50ms if websocket is not connected, wait for reconnection
        with self.__ws_mutex:
            self.__websocket.send(json.dumps(data))

    def start_websocket(self, subscribe_callback = None, 
                                order_update_callback = None,
                                socket_open_callback = None,
                                socket_close_callback = None,
                                socket_error_callback = None,
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
        
        # Create websocket session
        data = {"loginType" : "API"}
        self.__api_call_helper('createWsSession', Requests.POST, data)

        # Create websocket connection
        self.__websocket_connected = False
        self.__websocket = websocket.WebSocketApp(self.__urls['ws'],
                                                    on_data=self.__on_data_callback,
                                                    on_error=self.__on_error_callback,
                                                    on_close=self.__on_close_callback,
                                                    on_open=self.__on_open_callback)
        self.__ws_thread = threading.Thread(target=self.__ws_run_forever)
        self.__ws_thread.daemon = True
        self.__ws_thread.start()

        # Send initial data 
        data = {"susertoken": hashlib.sha256(hashlib.sha256(self.__session_id.encode('utf-8')).hexdigest().encode('utf-8')).hexdigest(),
                "t": "c",
                "actid": self.__username + "_API",
                "uid": self.__username + "_API",
                "source": "API"
                }
        self.__ws_send(data)

    def get_profile(self):
        """ Get profile """
        exch_dt = {"nse_cm"    : "NSE",
                    "bse_cm"    : "BSE",
                    "nse_fo"    : "NFO",
                    "mcx_fo"    : "MCX",
                    "cde_fo"    : "CDS",
                    "mcx_sx"    : "BFO",
                    "bcs_fo"    : "BCD",
                    "nse_com"   : "NCO",
                    "bse_com"   : "BCO"}
        profile = self.__api_call_helper('profile', Requests.GET)
        x = profile['exchEnabled'].split("|")
        self.__enabled_exchanges = [exch_dt[i] for i in x if i in exch_dt]
        return profile

    def get_balance(self):
        """ Get balance/margins """
        return self.__api_call_helper('getRmsLimits', Requests.GET)

    def get_daywise_positions(self):
        """ Get daywise positions """
        return self.__api_call_helper('positions', Requests.POST, {"ret" : "DAY"})

    def get_netwise_positions(self):
        """ Get netwise positions """
        return self.__api_call_helper('positions', Requests.POST, {"ret" : "NET"})

    def get_holding_positions(self):
        """ Get holdings positions """
        return self.__api_call_helper('holdings', Requests.GET)

    def get_order_history(self, order_id=None):
        """ Get order history """
        if(order_id == None):
            return self.__api_call_helper('fetchOrder', Requests.GET)
        else:
            return self.__api_call_helper('orderHistory', Requests.POST, {'nestOrderNumber': order_id})
    
    def get_scrip_info(self, instrument):
        """ Get scrip information """
        data = {'exch': instrument.exchange, 'symbol': instrument.token}
        return self.__api_call_helper('scripDetails', Requests.POST, data)

    def get_trade_book(self):
        """ get all trades """
        return self.__api_call_helper('fetchTrade', Requests.GET)

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
        return prod_type

    def __get_complexity_str(self, order_type):
        complexity = "Regular"
        if(order_type == OrderType.BracketOrder):
            complexity = 'BO'
        elif(order_type == OrderType.AfterMarketOrder):
            complexity = 'AMO'
        return complexity

    def place_order(self, transaction_type, instrument, quantity, order_type,
                    product_type, price=0.0, trigger_price=None,
                    stop_loss=None, target=None, trailing_sl=None,
                    disclosed_quantity = None,
                    order_tag = None):
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
        complexity = self.__get_complexity_str(order_type)
        # construct order object after all required parameters are met
        self.__order_tag += 1
        order = [{  "discqty"        : quantity if disclosed_quantity == None else disclosed_quantity,
                    "exch"           : instrument.exchange,
                    "transtype"      : transaction_type.value, 
                    "ret"            : "DAY",
                    "prctyp"         : order_type.value,
                    "qty"            : quantity,
                    "symbol_id"      : instrument.token,
                    "trading_symbol" : instrument.symbol,
                    "price"          : price,
                    "trigPrice"      : trigger_price,
                    "pCode"          : prod_type,
                    "complexty"      : complexity,
                    "orderTag"       : self.__order_tag if(order_tag == None) else order_tag
                }]

        if order_type is OrderType.BracketOrder:
            if not isinstance(stop_loss, float):
                raise TypeError("Required parameter stop_loss is not of type float")

            if not isinstance(target, float):
                raise TypeError("Required parameter target is not of type float")
            
            order["stopLoss"] = stop_loss
            order["target"] = target

            if trailing_sl is not None and not isinstance(trailing_sl, int):
                raise TypeError("Optional parameter trailing_sl not of type int")
            elif trailing_sl is not None:
                order["trailing_stop_loss"] = trailing_sl

        return self.__api_call_helper("placeOrder", Requests.POST, order)

    def modify_order(self, transaction_type, instrument, product_type, order_id, order_type, quantity, price=0.0,
                     trigger_price=0.0):
        """ modify an order, transaction_type, instrument, product_type, order_id, order_type & quantity is required, 
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

        if product_type is None:
            raise TypeError("Required parameter product_type not of type ProductType")

        if price is not None and not isinstance(price, float):
            raise TypeError("Optional parameter price not of type float")

        if trigger_price is not None and not isinstance(trigger_price, float):
            raise TypeError("Optional parameter trigger_price not of type float")

        prod_type = self.__get_product_type_str(product_type, instrument.exchange)
        # construct order object with order id
        order = {   "exch"           : instrument.exchange,
                    "nestOrderNumber": order_id,
                    "transtype"      : transaction_type.value, 
                    "prctyp"         : order_type.value,
                    "qty"            : quantity,
                    "price"          : price,
                    "trigPrice"      : trigger_price,
                    "pCode"          : prod_type
                }
        return self.__api_call_helper('modifyOrder', Requests.POST, order)

    def cancel_order(self, order_id, leg_order_id=None):
        """ Cancel single order """
        if(leg_order_id == None):
            return self.__api_call_helper('cancelOrder', Requests.POST, {'nestOrderNumber': order_id})
        else:
            return self.__api_call_helper('exitBracketOrder', Requests.POST, {"nestOrderNumber" : order_id, "symbolOrderId" : leg_order_id, "status" : "open"})

    def square_off(self, instrument, quantity, product_type):
        """ Square Off positions """
        if not isinstance(instrument, Instrument):
            raise TypeError("Required parameter instrument not of type Instrument")

        if not isinstance(quantity, int):
            raise TypeError("Required parameter quantity not of type int")

        if product_type is None:
            raise TypeError("Required parameter product_type not of type ProductType")

        prod_type = self.__get_product_type_str(product_type, instrument.exchange)
        order = {   "exchSeg"   :   instrument.exchange,
                    "pCode"     :   prod_type,
                    "netQty"    :   quantity,
                    "tockenNo"  :   instrument.token,
                    "symbol"    :   instrument.symbol
                }
        return self.__api_call_helper('sqrOfPosition', Requests.POST, order)
        
    def subscribe_market_status_messages(self):
        """ Subscribe to market messages @TODO need to update after alice implements market status messages """
        pass

    def get_market_status_messages(self):
        """ Get market messages """
        return self.__market_status_messages
    
    def subscribe_exchange_messages(self):
        """ Subscribe to exchange messages @TODO need to update after alice implements exchange messages """
        pass

    def get_exchange_messages(self):
        """ Get stored exchange messages """
        return self.__exchange_messages
    
    def subscribe(self, instrument, live_feed_type):
        """ subscribe to the current feed of an instrument or multiple instruments """
        if(type(live_feed_type) is not LiveFeedType):
            raise TypeError("Required parameter live_feed_type is not of type LiveFeedType")
        subscribe_string = ""
        if (isinstance(instrument, list)):
            for _instrument in instrument:
                if not isinstance(_instrument, Instrument):
                    raise TypeError("Required parameter instrument is not of type Instrument")
                subscribe_string += f"#{_instrument.exchange}|{int(_instrument.token)}"
                self.__subscribers[_instrument] = live_feed_type
        else:
            if not isinstance(instrument, Instrument):
                raise TypeError("Required parameter instrument is not of type Instrument")
            subscribe_string = f"#{instrument.exchange}|{int(instrument.token)}"
            self.__subscribers[instrument] = live_feed_type
        if(live_feed_type == LiveFeedType.TICK_DATA):
            tick_type = 't' 
        elif(live_feed_type == LiveFeedType.DEPTH_DATA):
            tick_type = 'd' 
        subscribe_string = subscribe_string[1:] # remove the first '#' symbol
        data = {'k' : subscribe_string, 't' : tick_type}
        self.__ws_send(data)

    def unsubscribe(self, instrument, live_feed_type):
        """ unsubscribe to the current feed of an instrument or multiple instruments """
        if(type(live_feed_type) is not LiveFeedType):
            raise TypeError("Required parameter live_feed_type is not of type LiveFeedType")
        subscribe_string = ""
        if (isinstance(instrument, list)):
            for _instrument in instrument:
                if not isinstance(_instrument, Instrument):
                    raise TypeError("Required parameter instrument is not of type Instrument")
                subscribe_string = f"#{_instrument.exchange}|{int(_instrument.token)}"
                if(_instrument in self.__subscribers): del self.__subscribers[_instrument]
        else:
            if not isinstance(instrument, Instrument):
                raise TypeError("Required parameter instrument is not of type Instrument")
            subscribe_string = f"#{instrument.exchange}|{int(instrument.token)}"
            if(instrument in self.__subscribers): del self.__subscribers[instrument]
        if(live_feed_type == LiveFeedType.TICK_DATA):
            tick_type = 'u' 
        elif(live_feed_type == LiveFeedType.DEPTH_DATA):
            tick_type = 'ud' 
        subscribe_string = subscribe_string[1:] # remove the first '#' symbol
        data = {'k' : subscribe_string, 't' : tick_type}
        self.__ws_send(data)

    def get_all_subscriptions(self):
        """ get the all subscribed instruments """
        return self.__subscribers
    
    def __resubscribe(self):
        tick = []
        depth = []
        for key, value in self.get_all_subscriptions().items():
            if(value == LiveFeedType.TICK_DATA):
                tick.append(key) 
            elif(value == LiveFeedType.DEPTH_DATA):
                depth.append(key) 
        if(len(tick) > 0):
            self.subscribe(tick, LiveFeedType.TICK_DATA)
        if(len(depth) > 0):
            self.subscribe(depth, LiveFeedType.DEPTH_DATA)

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
            logger.warning(f"Cannot find symbol {symbol} in master contract {exchange}")
            return None
        return master_contract[symbol]
    
    def get_instrument_for_fno(self, symbol, expiry_date, is_fut=False, strike=None, is_CE = False, exchange = 'NFO'):
        """ get instrument for FNO """
        res = self.search_instruments(exchange, symbol)
        if(res == None):
            return
        matches = []
        for i in res:
            sp = i.name.split(' ')
            if(sp[0] == symbol):
                if(i.expiry == expiry_date):
                    matches.append(i)
        for i in matches:
            if(is_fut == True):
                if('FUT' in i.symbol):
                    return i
            else:
                sp = i.name.split(' ')
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

    def historical_data(self, instrument, ffrom, to, type):
        """ Get Historical Data """
        if not isinstance(instrument, Instrument):
            raise TypeError("Required parameter instrument is not of type Instrument")
        if not isinstance(ffrom, datetime.datetime):
            raise TypeError("Required parameter 'ffrom' is not of type datetime")
        if not isinstance(to, datetime.datetime):
            raise TypeError("Required parameter 'to' is not of type datetime")
        if not isinstance(type, HistoricalDataType):
            raise TypeError("Required parameter 'type' is not of type HistoricalDataType")
        data = {"token"     : instrument.token,
                "resolution": type.value, 
                "from"      : int(datetime.datetime.timestamp(ffrom) * 1000), 
                "to"        : int(datetime.datetime.timestamp(to) * 1000),
                "exchange"  : instrument.exchange}
        return self.__api_call_helper('history', Requests.POST, data)

    def get_master_contract(self, exchange):
        """ Get master contract """
        return self.__master_contracts_by_symbol[exchange]

    def __get_master_contract(self, exchange):
        """ returns all the tradable contracts of an exchange
            placed in an OrderedDict and the key is the token
        """
        # See if master contracts are present in local.
        present = False
        dr = tempfile.gettempdir()
        tmp_file = os.path.join(dr, f"alice_blue_master_contract_{exchange}.json")
        if(os.path.isfile(tmp_file) == True):
            with open(tmp_file, 'r') as fo:
                d = json.loads(fo.read())
                if(datetime.datetime.now(pytz.timezone("Asia/Kolkata")).date() == datetime.datetime.strptime(d["contract_date"], "%d-%m-%Y").date()):
                    logger.info(f'Took master contracts from local for exchange: {exchange}')
                    body = d
                    present = True
        # if not download from alice server
        if(present == False):
            logger.info(f'Downloading master contracts for exchange: {exchange}')
            body = self.__api_call_helper('master_contract', Requests.GET, params={'exchange': exchange})
            # Write to temp file
            with open(tmp_file, 'w') as fo:
                fo.write(json.dumps(body))
        for exch in body:
            if(exch != "contract_date"):
                for scrip in body[exch]:
                    # convert token
                    token = int(scrip["token"])
        
                    # convert symbol to upper
                    if("trading_symbol" in scrip):
                        symbol = scrip["trading_symbol"]
                    else:
                        symbol = scrip["symbol"]
        
                    # convert expiry to none if it's non-existent
                    if("expiry_date" in scrip):
                        expiry = datetime.datetime.fromtimestamp(scrip['expiry_date']/1000, tz=pytz.utc).date()
                    else:
                        expiry = None
        
                    # convert lot size to int
                    lot_size = None
                    if("lot_size" in scrip):
                        lot_size = scrip["lot_size"]
                        
                    # Name  
                    name = None
                    if("formatted_ins_name" in scrip):
                        name = scrip["formatted_ins_name"]
                    
                    instrument = Instrument(exch, token, symbol, name, expiry, lot_size)
                    if(exch not in self.__master_contracts_by_token):
                        self.__master_contracts_by_token[exch] = {}
                    if(exch not in self.__master_contracts_by_symbol):
                        self.__master_contracts_by_symbol[exch] = {}
                    self.__master_contracts_by_token[exch][token] = instrument
                    self.__master_contracts_by_symbol[exch][symbol] = instrument

    def __api_call_helper(self, name, http_method, data=None, params=None):
        # helper formats the url and reads error codes nicely
        url = self.__urls[name]
        if params is not None:
            url = url.format(**params)
        response = self.__api_call(url, http_method, data)
        if response.status_code != 200:
            raise requests.HTTPError(response.text)
        return response.json()

    def __api_call(self, url, http_method, data):
        # Update header with Session ID
        headers = { "Content-Type"  : "application/json",
                    "Authorization" : f"Bearer {self.__username} {self.__session_id}"}
        r = None
        if http_method is Requests.POST:
            r = requests.post(url, json=data, headers=headers)
        elif http_method is Requests.DELETE:
            r = requests.delete(url, headers=headers)
        elif http_method is Requests.PUT:
            r = requests.put(url, json=data, headers=headers)
        elif http_method is Requests.GET:
            r = requests.get(url, headers=headers)
        return r
