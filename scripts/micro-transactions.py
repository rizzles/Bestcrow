from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import pprint
import requests
import tornado.escape

bitcoin = AuthServiceProxy("http://bitcoin:3jf8aAAFh7z7gk22AAd77vhaB788@127.0.0.1:8332")
mikes = "mgsUnLsMhphUyFiiCDBa6UWqhDivWaNwSe"
mine = "mpbJSfca2Z5vwB5ogMhPTJ3DBx2fZDMkGz"
pubkeymike = "03985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d"
pubkeymine = "03133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df061"
multiaddress = "2NC9uL5Qcnt4awdTBi3jB6ADPVdvwP9iR8L"
redeemscript = "522103133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df0612103985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d52ae"

company1 = "mrTRKLaDF86gLdKnacjxkXJdRFS6S8poTY"
company2 = "mmQDjcub4ozy7e7ET6Yx75MDcLQHdhofbU"
company3 = "mwDZvcxXWNWf9L16FmKWcLSJkpGaYcJaxA"
company4 = "n3TCEYhf94rmbXf4X6YUqq4QkBwNH93nqg"


# Get unspents from insight
r = requests.get('http://52.1.141.196:3001/api/addr/%s/utxo'%multiaddress)
r = tornado.escape.json_decode(r.text)[0]
print r['txid']



## input tx into multi-wallet
print "Creating spend transaction from multi address"
tx = [{"txid":r['txid'] ,"vout":r['vout'],"scriptPubKey":r['scriptPubKey'],"redeemScript":"522103133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df0612103985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d52ae"}]


print ""
print "TX", tx
# 2 cents
trans = bitcoin.createrawtransaction(tx, {multiaddress:0.004, company1:0.0001, company2:0.0002, company3:0.0003, company4:0.0003})
print trans


print ""
print "Signing raw transaction"
signed1 = bitcoin.signrawtransaction(trans, tx, ["cRuMbJGz3WN7cVzbUe4iLfT7g5hPZX4eoukYeAwdXsVNjkbRBcJ3"])
print signed1


print ""
print "Signing raw2 transaction"
signed2 = bitcoin.signrawtransaction(signed1['hex'], tx, ["cMjdH4LvCgtL1LkJ943WVng7rAe1Wi9rV8zZradncMJoeFPTtHBQ"])
print signed2


print ""
print "Sending raw transaction"
#print bitcoin.sendrawtransaction(signed2['hex'])
