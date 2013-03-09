import sys
import random

units = ['BTC', 'USD']
rate  = [1, 40]
account = [0, 500]

while True:
	try:
		d = random.gauss(0, 0.05)
		if d < 0:
			rate[1] *= (d+1)
		elif d > 0:
			rate[1] /= (1-d)

		print ''
		print "Account:\t%s,\t\t%s" % tuple([ "%.3f %s" % x for x in zip(account, units)])
		print "Value:  \t=%.2f %s,\t\t=%.2f %s" % (account[0] * rate[1], units[1], account[1] / rate[1], units[0])
		print 'Rate:   \t%s' % '\t=\t'.join([ "%.3f %s" % x for x in zip(rate, units)])

		userinput = sys.stdin.readline().strip()
		(action, amount, unit) = (userinput.split(" ")  + [None]*3)[0:3]

		if userinput == "":
			continue
			
		if action is None:
			continue

		if action in ['buy', 'b']:
			action = 'buy'
		else:
			action = 'sell'

		if unit in ['usd', 'USD', '$', 'dollar', 'd']:
			unit = 'USD'
		elif unit in ['btc', 'BTC', 'b']:
			unit = 'BTC'

		if amount in ['all', 'a']:
			amount = 'all'

		if unit == 'BTC':
			if amount == 'all':
				amount = account[0]
			usd = float(amount) * rate[1]

		if unit == 'USD':
			if amount == 'all':
				amount = account[1]

			usd = float(amount)

		btc = usd / rate[1]

		if action == 'sell' and unit == 'USD' or action == 'buy' and unit == 'BTC':
			do = 'sell_usd'
		if action == 'buy' and unit == 'USD' or action == 'sell' and unit == 'BTC':
			do = 'buy_usd'

		if do == 'sell_usd':
			account[0] += btc
			account[1] -= usd
		if do == 'buy_usd':
			account[0] -= btc
			account[1] += usd

	except KeyboardInterrupt:
		print "Done"
		break