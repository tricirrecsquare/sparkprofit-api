# sparkprofit-api

 
 This module will provide very basic access to the game www.sparkprofit.com (stockmarket simulation).
 It's able to get prices and to store them into an sql database, open/close trades and to keep track of open trades.

 Possible applications for this 'api' cloud be algorithmic trading and an advanced charting interface for the game(see my other repositories).

 If you have any questions or ideas, feel free to contact me or to make a pull request.

 Example use of the module to get all availible price data from the server and to store them into the sql database.

    from Sparkprofit import Sparkprofit

    sp = Sparkprofit()
    sp.login('testuser42@mailinator.com', 'a123456')

    #enable the instance to interact with all the different markets provided by the game
    sp.set_up_all_markets()

    #iterate over all the standard time intervalls for the price
    for intervall in sp.INTERVALLS:

        #iterate over alle the markets that we have set up
        for m in sp.markets:
            print 'Fetching data for {m}{int}'.format(m=m, int=intervall)
            
            #fetch as much price data from the server as possible and store it to an sqlite database
            sp.markets[m].get_historical_data(intervall)
