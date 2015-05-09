import bitcoin
from bitcoin.core import COIN, b2lx
import bitcoin.wallet
import bitcoin.rpc

bitcoin.SelectParams('testnet')


print 0.003 * COIN

rpc = bitcoin.rpc.Proxy()
balance = rpc.getbalance()

print balance
balance = float(balance) % float(COIN)
print "%.8f"%balance
