#ignore pylinter invalid constant name, caused by wrong scope
# pylint: disable-msg=C0103

from Sparkprofit import Sparkprofit
import time
#suppress urrlib2 InsecurePlatformWarning
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

def print_active_trades():
    if sp.user.active_trades:
        print 'Active trades: \n'
        for trade in sp.user.active_trades:
            print 'market: ' + trade.market_id
            print 'score: ' + str(trade.last_score)
            print 'take profit: ' + str(trade.take_profit)
            print 'stop loss: ' + str(trade.stop_loss)
            print 'leverage: ' + str(trade.leverage)
            print '\n'
    else:
        print 'No active trades found!'

sp = Sparkprofit()
#login our test user
sp.login('testuser42@mailinator.com', 'a123456')
#enable the instance to interact with all the different
#markets provided by the game
sp.set_up_all_markets()
print_active_trades()

#if you want to end a trade just select the market and
#close trade, since we can just have one trade
#per market at a time
#sp.markets['BTCUSD'].close_trade()

while True:
    if not sp.user.active_trades:
        btcusd = sp.markets['BTCUSD']
        price = btcusd.get_price(60000)
        #pay attention that your stop loss and take profit
        #are with in the limits set by sparkprofit
        btcusd.open_trade(1.1*price, 0.95*price, 1)
    print_active_trades()
    time.sleep(10)
