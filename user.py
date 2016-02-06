#ignore pylinter invalid constant name, caused by wrong scope
# pylint: disable-msg=C0103
import requests
import json
import trade as sparkprofit_trade

class User(object):

    PSubmissionHistoryRequest = 'https://sparkprofit.com/data/gain/subHistory/PSubmissionHistoryRequest.json'
    PBetHistoryRequest = 'https://sparkprofit.com/data/gain/betHistory/PBetHistoryRequest.json'

    email = ''
    password = ''
    screen_name = ''
    publicId = ''
    invariantId = ''
    active_trades = []
    trade_count = 0

    def __init__(self, **kwargs):
        #get user identifier data from the login answer
        self.screen_name = kwargs['rjson']['user']['identifier']['screenName']
        self.publicId = kwargs['rjson']['user']['identifier']['publicId']
        self.invariantId = kwargs['rjson']['user']['identifier']['invariantId']
        self.email = kwargs['email']
        self.password = kwargs['password']
        self.parent_instance = kwargs['instance']
        self.get_active_trades()

    #get all active trades the user has and add trade objects to the active trades
    def get_active_trades(self):
        #params = {'userId':str(self.email), 'authCode':str(self.password)}
        params = {'beforeMs':0, 'userIdentifier':{'invariantId':self.invariantId,
         'publicId':self.publicId, "screenName":self.screen_name}}
        #{"beforeMs":0,"userIdentifier":{"invariantId":"241623","publicId":"CbPzkq","screenName":"testuser42"}}
        #r = self.parent_instance.session.post(self.PSubmissionHistoryRequest, data=json.dumps(params))
        r = self.parent_instance.session.post(self.PBetHistoryRequest, data=json.dumps(params))
        r.encode = 'utf-8'

        rjson = r.json()
        if 'submissions' not in rjson.keys():
            return None
        self.active_trades = list()
        #iterate the submisson history the server provides
        for trade in rjson['submissions']:
            #get the active trades
            if int(trade['score']['status']) == 1:
                if len(self.active_trades) == 0:
                    self.active_trades.append(sparkprofit_trade.Trade(self, trade))
                else:
                    for t in self.active_trades:
                        #check if this is a new trade and append it or just refresh the current score
                        if int(trade['id']) == t.trade_id:
                            t.get_current_score()
                        else:
                            new_trade = sparkprofit_trade.Trade(self, trade)
                            self.active_trades.append(new_trade)
                            self.trade_count += new_trade.leverage
                            new_trade = None