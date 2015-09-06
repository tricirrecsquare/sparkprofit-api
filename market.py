#ignore pylinter invalid constant name, caused by wrong scope
# pylint: disable-msg=C0103

import requests
import json
import time
import datetime

from errors import LoginFailedException, TradeLimitExceededException, InvalidPriceRangeException, UnkownErrorExceprion

class Market(object):

    PAggTradeHistoryRequest = 'https://sparkprofit.com/data/gain/tradeHistory/PAggTradeHistoryRequest.json'
    PCancellation = 'https://sparkprofit.com/data/gain/cancellation/PCancellation.json'
    PLevelSubmission = 'https://sparkprofit.com/data/gain/submission/PLevelSubmission.json'

    market_id = ''
    parent_instance = None
    active_trade = None
    entry_costs = 0

    def __init__(self, **kwargs):
        self.market_id = kwargs['market_id']
        self.parent_instance = kwargs['instance']
        for t in self.parent_instance.user.active_trades:
            if t.market_id == self.market_id:
                self.active_trade = t
                break

    #get the latest price for this market
    #parm: resolutionMS - timeframe in milliseconds
    def get_price(self, resolutionsMs):
        try:
            params = {"tradeable":self.market_id,
                    "resolutionsMs":[resolutionsMs],
                    "buckets":1371,
                    "centerMs":0,
                    "fromMs": 0,
                    "requestType":0}

            r = self.parent_instance.session.post(self.PAggTradeHistoryRequest,
                                                data=json.dumps(params))
            r.encoding = 'urf-8'
            rjson = r.json()

            if 'success' in rjson.keys():
                if rjson['success'] == False:
                    raise LoginFailedException(rjson['failureDetails'])
            else:
                return rjson['aggTrades'][0]['close']
        except LoginFailedException as e:
            print e.text
        except requests.exceptions.ConnectionError as e:
            print e
            exit(1)

    #fetch all historical price data for this market that the server proviedes in the resolution of resolutionMs
    #parm: resolutionMs - timeframe of the data in milliseconds
    #[60000,180000,600000,1200000,3600000,10800000,28800000]
    def get_historical_data(self, resolutionsMs):

        params = {"tradeable":self.market_id,
                "resolutionsMs":[resolutionsMs],
                "buckets":15000,
                "centerMs":0,
                "fromMs": 0,
                "requestType":0}

        r = self.parent_instance.session.post(self.PAggTradeHistoryRequest,
                                             data=json.dumps(params))
        r.encoding = 'urf-8'
        rjson = r.json()['aggTrades']

        last_ts = self.get_last_ts_from_db(rjson[0]['tradeable'],
                                         int(resolutionsMs))
        db_entry_count = 0

        for dataset in rjson:
            if int(last_ts) < int(dataset['startMs']):
                self.write_dataset_to_db(dataset)
                db_entry_count += 1

        table_name = str(rjson[0]['tradeable']) + str(resolutionsMs)
        print "Added {count} new entrie(s) to {tn}"\
                .format(count=db_entry_count, tn=table_name)


    def get_last_ts_from_db(self, instrument, intervall):
        table_name = str(instrument.replace(':', '')).lower() + str(intervall)
        conn = self.parent_instance.database_connection
        with conn:
            cursor = conn.cursor()
            query = "SELECT MAX(timestamp) FROM {table_name}".format(
                                                table_name=table_name)
            cursor.execute(query)
            last_ts = cursor.fetchall()
            if last_ts[0][0] is not None:
                return last_ts[0][0]
            else:
                return 0

    # key structure of the database
    #(timestamp INT, vwap REAL, qty INT, high REAL, low REAL, open REAL,
    #close REAL, tradeCount INT, startMS INT, endMs INT)
    def write_dataset_to_db(self, dataset):
        conn = self.parent_instance.database_connection
        intervall = dataset['lengthMs']
        instrument = dataset['tradeable']
        table_name = str(instrument.replace(':', '')).lower() + str(intervall)
        startMs = str(dataset['startMs'])
        vwap = str(dataset['vwap'])
        qty = str(dataset['qty'])
        high = str(dataset['high'])
        low = str(dataset['low'])
        open_price = str(dataset['open'])
        close = str(dataset['close'])
        tc = str(dataset['tradeCount'])
        endMs = str(dataset['endMs'])
        with conn:
            cursor = conn.cursor()
            query = """INSERT INTO {tn} VALUES({ts}, {vwap}, {qty}, {high},
                    {low}, {open}, {close}, {tc}, {startMs}, {endMs})""".format(
                    tn=table_name, ts=startMs, vwap=vwap, qty=qty, high=high,
                    low=low, open=open_price, close=close, tc=tc,
                    startMs=startMs, endMs=endMs)
            cursor.execute(query)


    #fetch the newest price data from the server and write it to the database
    def log_price_data(self, resolutionsMs):
        while True:
            try:
                params = {"tradeable":self.market_id,
                        "resolutionsMs":[resolutionsMs],
                        "buckets":1371,
                        "centerMs":0,
                        "fromMs": 0,
                        "requestType":0}

                r = self.parent_instance.session.post(self.PAggTradeHistoryRequest,
                                                    data=json.dumps(params))
                r.encoding = 'urf-8'
                rjson = r.json()

                if 'success' in rjson.keys():
                    if rjson['success'] == False:
                        raise LoginFailedException(rjson['failureDetails'])
                else:
                    dataset = rjson['aggTrades'][0]
                    last_ts = self.get_last_ts_from_db(self.market_id, resolutionsMs)
                    if int(last_ts) < int(dataset['startMs']):
                        self.write_dataset_to_db(dataset)
                        if self.parent_instance.DEBUG:
                            print '[*]Added a new dataset for ' + self.market_id + str(resolutionsMs)
            except LoginFailedException as e:
                print e.text
            except requests.exceptions.ConnectionError as e:
                print e
                exit(1)


            time.sleep(resolutionsMs/1000)

    def refresh_active_trades(self):
        self.parent_instance.user.get_active_trades()

    def open_trade(self, tp, sl, leverage):
        #check if there is an open trade for this market
        if self.active_trade is not None:
            raise TradeLimitExceededException('[!]Can not open a new trade in ' + str(self.market_id) + '. Trade limit for this market exceeded!')
        #check the trade limit of the user, curennt limit  is 6, where leveraged trades count as multiple trades
        if self.parent_instance.user.trade_count + leverage > 6:
            raise TradeLimitExceededException('[!]Can not open a new trade in ' + str(self.market_id) + '. Global trade limit exceeded')

        params = {"startMs":time.time()*1000,
                    "market":str(self.market_id),
                    "predictions":[
                        {"expiryMs":0,
                        "prediction":float(tp),
                        "stopLoss":float(sl)}],
                    "clientArrPx":self.get_price(60000),
                    "sendCompletionNotif":False,
                    "confidence":int(leverage),
                    "submissionMetaData":{"chartInverted":False,
                                        "zoomLevelMs":127862616},
                    "sentTimeMs":time.time()*1000}

        r = self.parent_instance.session.post(self.PLevelSubmission,
                                             data=json.dumps(params))
        rjson = r.json()
        #check if the server opend a trade
        if 'success' in rjson:
            if rjson['success'] == False:
                if 'range' in rjson['message'].lower():
                    raise InvalidPriceRangeException(rjson['message'])
        else:
            #update the trades and the trade count of the user
            self.parent_instance.user.get_active_trades()
            #assign the new trade to the user
            for t in self.parent_instance.user.active_trades:
                if t.market_id == self.market_id:
                    self.active_trade = t
                    break
            if self.parent_instance.DEBUG:
                print '[!]New ' + self.active_trade.get_direction()[0] + ' trade in ' + self.market_id + '.'

    def close_trade(self):
        #check if there is an open trade for this market
        if self.active_trade is None:
            raise AttributeError('Can not close a trade in ' + self.market_id + ', beause there is no trade!')
        active_trade_id = self.active_trade.trade_id
        #make the request to cllose the trade
        params = {"submissionId": self.active_trade.trade_id,
                    "cancellation": True,
                    "sentTimeMs": time.time()*1000}
        r = self.parent_instance.session.post(self.PCancellation,
                                         data=json.dumps(params))
        rjson = r.json()
        #check if the trade was closed
        if rjson['status'] == 3:
            #remove the trade from the active trades
            self.active_trade = None
            self.parent_instance.user.get_active_trades()
            if self.parent_instance.DEBUG:
                print '[!]Closed position in ' + self.market_id + ' with a win/loss of: ', rjson['prestige']
        else:
            raise UnkownErrorExceprion('Unkown error while closing a trade in ' + self.market_id)
