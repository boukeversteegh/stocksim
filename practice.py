import sys
import random

class RandomRateGenerator:
	def __init__(self, rates, volatilities):
		self.rates = {}
		self.volatilities = {}		
		self.initialrates = {}
		for unit in rates:
			self.rates[unit] = float(rates[unit])
			self.initialrates[unit] = float(rates[unit])
			self.volatilities[unit] = float(volatilities[unit])

			
		
	def getRate(self):
		return self.rates

	def update(self):
		for unit in self.rates:
			rate = self.rates[unit]
			d = random.gauss(0, self.volatilities[unit])
			if d < 0:
				rate *= (d+1)
			elif d > 0:
				rate /= (1-d)
			self.rates[unit] = rate
		return self.rates


class Exchange:
	def __init__(self, rategenerator):
		self.rategenerator = rategenerator
		self.rates = self.rategenerator.getRate()

	def convert(self, amount, fromunit, tounit):
		rate = self.rates[tounit] / self.rates[fromunit]
		toamount = amount * rate
		return toamount

	def exchange(self, account, amount, fromunit, tounit):
		log("Exchanging %.2f %s into %s" % (amount, fromunit, tounit))
		amountbought = self.convert(amount, fromunit, tounit)

		account.withdraw(amount, fromunit)
		account.deposit(amountbought, tounit)

	def updateRates(self):
		self.rates = self.rategenerator.update()

class InsufficientFundsException(Exception): pass

class Account:
	def __init__(self, **balance):
		self.balance = {}
		for unit in balance:
			self.balance[unit] = float(balance[unit])

	def deposit(self, amount, unit):
		log('Depositing %.2f %s' % (amount, unit))
		self.balance.setdefault(unit, 0)
		self.balance[unit] += amount

	def withdraw(self, amount, unit):
		log('Withdrawing %.2f %s' % (amount, unit))
		if unit not in self.balance:
			raise InsufficientFundsException()
		if self.balance[unit] < amount:
			raise InsufficientFundsException()
		self.balance[unit] -= amount

	def get(self, unit):
		return self.balance.get(unit, 0)

	def getTotalValueIn(self, unit, exchange):
		totalvalue = self.get(unit)

		otherunits = [otherunit for otherunit in self.balance if otherunit != unit]

		for otherunit in otherunits:
			totalvalue += exchange.convert(self.get(otherunit), otherunit, unit)

		return totalvalue


class Strategy:
	def __init__(self, account, exchange):
		self.account = account
		self._exchange = exchange

	def exchange(self, *args, **kwargs):
		self._exchange.exchange(self.account, *args, **kwargs)


class ManualStrategy(Strategy):
	def normalizeUnit(self, text):
		aliases	= {'BTC':['bitcoin', 'b', 'btc'], 'USD': ['dollar', '$', 'd', 'usd']}
		for unit in aliases:
			if text.lower() in aliases[unit]:
				return unit

	def normalizeAction(self, text):
		if text in ['buy', 'b']:
			return 'buy'
		else:
			return 'sell'

	def normalizeAmount(self, amount):
		if amount.lower() in ['all', 'a']:
			return 'ALL'
		else:
			return float(amount)

	def run(self):
		userinput = sys.stdin.readline().strip()
		(action, amount, unit) = (userinput.split(" ")  + [None]*3)[0:3]

		if userinput == "":
			return
			
		if action is None:
			return

		action	= self.normalizeAction(action)
		amount	= self.normalizeAmount(amount)
		unit	= self.normalizeUnit(unit)

		log("%sing %s %s" % (action, str(amount), unit))

		if action == 'sell':
			fromunit = unit
			tounit = 'USD' if fromunit == 'BTC' else 'BTC'

			if amount == 'ALL':
				amount = self.account.get(fromunit)

		elif action == 'buy':
			tounit = unit
			fromunit = 'USD' if tounit == 'BTC' else 'BTC'

			if amount == 'ALL':
				# Buy all BTC
				# --> Sell all USD
				amount = self.account.get(fromunit)
			else:
				amount = self._exchange.convert(amount, tounit, fromunit)

				# (tounit, fromunit) = (fromunit, tounit)

		self.exchange(amount, fromunit, tounit)


class UnitBalanceStrategy(Strategy):
	def run(self):
		unit		= 'USD'
		otherunit	= 'BTC'

		totalvalue = self.account.getTotalValueIn(unit, self._exchange)
		half = totalvalue/2

		amount = self.account.get(unit)
		#sys.stdin.readline()

		sellfactor = 1
		buyfactor = 1

		if amount < half:
			buyamount = half - amount
			sellamount = self._exchange.convert(buyamount, unit, otherunit)
			self.exchange(sellamount*buyfactor, otherunit, unit)
		elif amount > half:
			sellamount = amount - half
			self.exchange(sellamount*sellfactor, unit, otherunit)

dolog = False
def log(text):
	if dolog:
		print "  " + light(Colors.BLACK) + text + Colors.RESET


class Colors:
	BLACK	= "\033[30m"
	RED		= "\033[31m"
	GREEN	= "\033[32m"
	BLUE	= "\033[34m"
	WHITE	= "\033[37m"
	RESET	= "\033[0m"

def light(color):
	return color.replace("m", ";1m")

def getOtherUnit(unit):
	otherunit = [u for u in rates.keys() if u != unit][0]
	return otherunit

def printStatus():
	totalvalues = {}
	for unit in rates:
		totalvalues[unit] = account.getTotalValueIn(unit, exchange)

	for unit in rates:
		amount = account.get(unit)
		otherunit = getOtherUnit(unit)

		column = (Colors.GREEN + "%.2f %s" + Colors.RESET + " = %.2f %s" + Colors.RESET) % (amount, unit, exchange.convert(amount, unit, otherunit), otherunit)
		print column.ljust(45),
		#print Colors.GREEN + str(amount), unit, Colors.RESET, "(=%.2f %s)\t" % (exchange.convert(amount, unit, otherunit), otherunit),
	
	print "Total: " + Colors.BLUE + " / ".join(["%.2f %s" % (totalvalues[unit], unit) for unit in totalvalues]), Colors.RESET
def printRates():
	print Colors.RED + " = ".join(["%.2f %s" % (exchange.rates[unit], unit) for unit in exchange.rates ]), Colors.RESET

from multiprocessing import Pool

def runexperiment(repetitions):
		rates			= {'BTC': 1, 'USD': 40}
		balance			= {'BTC': 0, 'USD': 500}
		volatilities	= {'BTC': 0, 'USD': float(sys.argv[3])}

		rategenerator	= RandomRateGenerator(rates, volatilities)
		exchange		= Exchange(rategenerator)
		account			= Account(**balance)

		#strategy	= ManualStrategy(account, exchange)
		strategy	= UnitBalanceStrategy(account, exchange)

		#account.withdraw(10, 'USD')
		#account.deposit(1, 'BTC')


		exchange.exchange(account, 250, 'USD', 'BTC')
		global stop
		try:
			for _ in range(0, repetitions):
					if stop:
						return
					#printRates()
					#printStatus()
					strategy.run()
					#printStatus()
					exchange.updateRates()
			
			value = account.getTotalValueIn('USD', exchange)
			hasprofit = (balance['USD'] < value)
			return {
				"hasprofit": hasprofit,
				"account": account,
				"exchange": exchange,
				"value": value
			}
		except KeyboardInterrupt:
			pass
try:
	stop = False
	numexperiments = int(sys.argv[1])
	repetitions = int(sys.argv[2])

	p = Pool(32)
	results = p.map(runexperiment, [repetitions]*numexperiments)
	
	hasprofitcount = sum([1 for result in results if result['hasprofit']])

	values = [result['value'] for result in results]
	averagevalue = sum(values) / len(values)

	successvalues = [result['value'] for result in results if result['hasprofit']]
	averagesuccessvalue = sum(successvalues) / len(successvalues)
	print "Success rate:         ", (hasprofitcount/float(numexperiments))
	print "Average value:        ", averagevalue, 'USD'
	print "Average success value:", averagesuccessvalue, 'USD'

except KeyboardInterrupt:
	sys.exit()

#exchange.exchange(account, 40, 'USD', 'BTC')