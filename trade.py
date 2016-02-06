import requests
import json

class Trade(object):

    PSubmissionHistoryRequest = 'https://sparkprofit.com/data/gain/subHistory/PSubmissionHistoryRequest.json'

    user = None
    market_id = ''
    stop_loss = 0
    take_profit = 0
    leverage = 0
    trade_id = 0
    last_score = 0

    def __init__(self, user, rjson):
        self.user = user
        self.market_id = rjson['bet']['market']
        self.stop_loss = float(rjson['bet']['stopLoss'])
        self.take_profit = float(rjson['bet']['prediction'])
        self.leverage = int(rjson['bet']['confidence'])
        self.trade_id = int(rjson['id'])
        #current value of the active trade
        self.last_score =  int(rjson['score']['scorePoints']/10)

    #refresh the current score for this trade_id
    def get_current_score(self):
        #print type(self.user), self.user
        params = {"beforeMs":0, "userIdentifier":{"invariantId":str(self.user.invariantId),
                                                "publicId":str(self.user.publicId),
                                                "screenName":str(self.user.screen_name)}}

        r = r = self.user.parent_instance.session.post(self.PSubmissionHistoryRequest, data=json.dumps(params))
        r.encode = 'utf-8'
        rjson = r.json()
        #iterate over all trades the server proviedes
        for sub in rjson['submissions']:
            #return the current score of this trade
            if int(sub['id']) == self.trade_id:
                return sub['score']['scoreData'][0]['points'] - self.user.parent_instance.market_ids[self.market_id]

    #check if the trade is long or short
    def get_direction(self):
        if self.take_profit > self.stop_loss:
            return ('long', 1)
        else:
            return ('short', 0)

