from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import pprint
import struct

bitcoin = AuthServiceProxy("http://bitcoin:3jf8aAAFh7z7gk22AAd77vhaB788@127.0.0.1:8332")
mikes = "mgsUnLsMhphUyFiiCDBa6UWqhDivWaNwSe"
mine = "mpbJSfca2Z5vwB5ogMhPTJ3DBx2fZDMkGz"
pubkeymike = "03985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d"
pubkeymine = "03133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df061"
multiaddress = "2NC9uL5Qcnt4awdTBi3jB6ADPVdvwP9iR8L"
redeemscript = "522103133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df0612103985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d52ae"

random = "mrTRKLaDF86gLdKnacjxkXJdRFS6S8poTY"
txtorandom = "bdad390ea15f1828466266a97d4f219ff2e64111a60cb204b30148b199260bd0"
random2 = "mmQDjcub4ozy7e7ET6Yx75MDcLQHdhofbU"
#print "NEW", bitcoin.getnewaddress("")
#print bitcoin.validateaddress(mine)



print ""
print "Addresses and priv keys in entire wallet"
addresses = bitcoin.getaddressesbyaccount("")
print addresses
for add in addresses:
    if not add[0] == '2':
        print bitcoin.dumpprivkey(add), add



## Create a multi-sig

print ""
print "Multi sig address"
adds = [pubkeymine, pubkeymike]
print "Addresses used", adds
multi = bitcoin.addmultisigaddress(2, adds)
multi = bitcoin.createmultisig(2, adds)
print multi

"""
print ""
print "Unspent transactions"
unspent = bitcoin.listunspent()
for x in unspent:
    print x
    print "---"
    if x['address'] == multiaddress:
        print "Unspent Multi: "
        print x


print ""
print "Creating spend transaction from multi address"
tx = [{"txid": "1b80cf8e54bb9273fa8d5dcffadb7c052d0009f923194b88cd11bbdc0ce15397","vout":0,"scriptPubKey":"a914cf68bc0b52453bb0daec05e10f097ee861b703df87","redeemScript":"522103133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df0612103985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d52ae"}]

#tx = [{"txid": "bdad390ea15f1828466266a97d4f219ff2e64111a60cb204b30148b199260bd0","vout":0,"scriptPubKey":"76a91477fe46d74ee5e946383ffd5823b0074241c85ef088ac","redeemScript":"522103133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df0612103985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d52ae"}]

print "TX", tx
trans = bitcoin.createrawtransaction(tx, {random2:0.007})
print trans



## messing with nLockTime. Transaction overwrites were disabled in btc 2 years ago. Not much there.

print tuple( struct.pack("!I", 329165) )
trans = trans[:-8]
trans += "df050500"
print trans

## Change sequence to 0
trans = trans.replace("ffffffff", "00000000")
print trans




print ""
print "Signing raw transaction"
signed1 = bitcoin.signrawtransaction(trans, tx, ["cRuMbJGz3WN7cVzbUe4iLfT7g5hPZX4eoukYeAwdXsVNjkbRBcJ3"])
print signed1


print ""
print ""
print "DECODE"
print pprint.pprint(bitcoin.decoderawtransaction(signed1['hex']))



signrawtransaction '' '[{"txid": "1b80cf8e54bb9273fa8d5dcffadb7c052d0009f923194b88cd11bbdc0ce15397","vout":0,"scriptPubKey":"a914cf68bc0b52453bb0daec05e10f097ee861b703df87","redeemScript":"522103133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df0612103985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d52ae"}]' '["cMjdH4LvCgtL1LkJ943WVng7rAe1Wi9rV8zZradncMJoeFPTtHBQ"]'



print ""
print "Signing raw2 transaction"
signed2 = bitcoin.signrawtransaction(signed1['hex'], tx, ["cMjdH4LvCgtL1LkJ943WVng7rAe1Wi9rV8zZradncMJoeFPTtHBQ"])
print signed2
"""


"""
print ""
print "Sending raw transaction"
print bitcoin.sendrawtransaction(signed2['hex'])
"""
