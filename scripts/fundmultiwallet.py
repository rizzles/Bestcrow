from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import pprint

random = "mz8p8gHyAWbi7ervPk7KoaBX8pGxXXeSXW"
random2 = "mmGK3hECmbsCZyAsyH4Dyg9bxir5Ggiid3"


bitcoin = AuthServiceProxy("http://bitcoin:3jf8aAAFh7z7gk22AAd77vhaB788@127.0.0.1:8332")
multiaddress = "2NBxJBiex6P9yLhVFCfZnuKhErsnDWDY26V"

try:
    print "sending funds"
    tx = bitcoin.sendtoaddress(multiaddress, 0.001, "multi")
except JSONRPCException, e:
    print "Error"
    print e.error

print tx
