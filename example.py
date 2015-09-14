#ignore pylinter invalid constant name, caused by wrong scope
# pylint: disable-msg=C0103

from Sparkprofit import Sparkprofit

sp = Sparkprofit()
#login our test user
sp.login('testuser42@mailinator.com', 'a123456')
#enable the instance to interact with all the different
#markets provided by the game
sp.set_up_all_markets()
#iterate over all the standard time intervalls for the price
for intervall in sp.INTERVALLS:
    #iterate over alle the markets that we have set up
    for m in sp.markets:
        print 'Fetching data for {m}{int}'.format(m=m, int=intervall)
        #fetch as much price data from the server as possible
        #and store it to an sqlite database
        sp.markets[m].get_historical_data(intervall)
