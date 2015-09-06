#ignore pylinter invalid constant name, caused by wrong scope
# pylint: disable-msg=C0103

import requests
import json
import time
import threading
import sqlite3
import os

import market
import user
from errors import LoginFailedException, TradeLimitExceededException, ServiceUnavailibleException

class Sparkprofit(object):
    DEBUG = True
    #all the time intervalls provided by the server
    INTERVALLS = [60000, 180000, 600000, 1200000, 360000, 10800000, 28800000]
    #the market ids contain special characters which are not valid for sql keys
    #this map will preserve the relation betwen  the original market ids
    #and the sql keys
    ID_MAP = {'BTCUSD':'BTCUSD', 'C:XAUUSD':'C:XAUUSD', 'CXAUUSD':'C:XAUUSD',
            'I:NKY225JPY':'I:NKY225JPY', 'INKY225JPY':'I:NKY225JPY',
            'AUDUSD':'AUDUSD', 'EURUSD':'EURUSD', 'C:CopperUSD':'C:CopperUSD',
            'CCopperUSD':'C:CopperUSD', 'USDJPY':'USDJPY',
            'I:SPX500USD':'I:SPX500USD', 'ISPX500USD':'I:SPX500USD',
            'I:EUSTX50EUR':'I:EUSTX50EUR', 'IEUSTX50EUR':'I:EUSTX50EUR',
            'C:UKOilUSD':'C:UKOilUSD', 'CUKOilUSD':'C:UKOilUSD',
            'GBPUSD':'GBPUSD'}

    PLogin = 'https://sparkprofit.com/data/gain/login/PLogin.json'
    PUserActivity = 'https://sparkprofit.com/data/gain/userActivity/PUserActivity.json'

    user = None
    market_ids = dict()
    markets = dict()
    session = None
    database_connection = None


    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type':'application/json'})
        self.database_connection = self.connect_to_database()

    #Log in the user and keep the session by linking it to the instance
    #and starting a conncetion keep alive
    def login(self, email, password):
        try:
            params = {'userId': str(email), 'authCode': str(password),
                'versionNumber':'1.0.539',
                'elapsedMs':'17788',
                'deviceId':''}
            r = self.session.post(self.PLogin, data=json.dumps(params))
            r.encode = 'utf-8'

            #check if the service is offline
            if r.status_code == 503:
                raise ServiceUnavailibleException('[!]The service is unavailible!')
            rjson = r.json()
            #check if the service is availible
            if 'failureCode' in rjson.keys():
                if rjson['failureCode'] == 1:
                    raise ServiceUnavailibleException(rjson['failureDetails'])
            if 'success' in rjson.keys():
                if rjson['success'] == False:
                    raise LoginFailedException(rjson['failureDetails'])
            else:
                self.user = user.User(rjson=rjson, instance=self,
                                    email=email, password=password)
                self.get_market_ids(rjson)
                if self.database_connection is None:
                    self.database_connection = self.create_database()
                if self.DEBUG:
                    print '[*]Logged in user: ' + str(self.user.screen_name)
                if len(self.user.active_trades) != 0:
                    for t in self.user.active_trades:
                        if t.market_id in self.market_ids:
                            self.set_up_market(t.market_id)

                t = threading.Thread(name='keep-alive',
                                    target=self.connection_keep_alive)
                t.setDaemon(True)
                t.start()

        except requests.exceptions.ConnectionError as e:
            print '[!] ', e
            exit(1)
        except ServiceUnavailibleException as e:
            print '[!] ', e.text
            exit(1)
        except LoginFailedException as e:
            print '[!] ', e.text


    #Send a keep live message to the server every 5 minutes
    def connection_keep_alive(self):
        while True:
            params = {"user":str(self.user.email),
                    "activeAt":time.time()*1000,
                    "activityType":3, "market":""}
            r = self.session.post(self.PUserActivity, data=json.dumps(params))
            rjson = r.json()
            if rjson['success'] == False:
                print '[!]Connection keep alive failed,!'
            elif self.DEBUG:
                print '[*]Sent keep-alive to server...'
            time.sleep(300)

    def create_database(self):
        conn = sqlite3.connect('sp_db.db')
        with conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE Instruments(Name TEXT)")
            #creat a table for every instrument and time intervall
            for m in self.market_ids.keys():
                for intervall in self.INTERVALLS:
                    cursor.execute("CREATE TABLE " + m.replace(':', '') + str(intervall) + "(timestamp INT PRIMARY KEY, vwap REAL, qty INT, high REAL, low REAL, open REAL, close REAL, tradeCount INT, startMS INT, endMs INT)")

        print '[*]Created new database in current working directory!'
        return conn


    def connect_to_database(self):
        if not os.path.isfile('sp_db.db'):
            return None
        else:
            if self.DEBUG:
                print '[*]Connected to database!'
            return sqlite3.connect('sp_db.db')

    #look up which markets the sparkprofit server proviedes
    #and save their entry costs
    def get_market_ids(self, rjson):
        markets = rjson['predictionMarkets']
        for m in markets:
            market_id = m['market']['id']
            self.market_ids[market_id] = m['levelGameEntryCostGPs']

    def set_up_market(self, market_id):
        self.markets[market_id] = market.Market(market_id=market_id,
                                        instance=self,
                                        entry_costs=self.market_ids[market_id])
        self.markets[market_id].get_price(60000)

    def set_up_all_markets(self):
        for market_id in self.market_ids:
            self.markets[market_id] = market.Market(market_id=market_id,
                                        instance=self,
                                        entry_costs=self.market_ids[market_id])
            self.markets[market_id].get_price(60000)

#test code to build up a price database
if __name__ == '__main__':
    sp = Sparkprofit()
    sp.login('testuser42@mailinator.com', 'a123456')
    sp.set_up_all_markets()
    for intervall in sp.INTERVALLS:
        for m in sp.markets:
            print 'Fetching data for {m}{int}'.format(m=m, int=intervall)
            sp.markets[m].get_historical_data(intervall)
