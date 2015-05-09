from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import pprint

bitcoin = AuthServiceProxy("http://bitcoin:3jf8aAAFh7z7gk22AAd77vhaB788@127.0.0.1:8332")

print ""
print "Addresses and priv keys in entire wallet"
addresses = bitcoin.getaddressesbyaccount("")
print addresses
for add in addresses:
    if not add[0] == '2':
        print bitcoin.dumpprivkey(add), add

print ""
print "Unspent transactions"
unspent = bitcoin.listunspent()
for x in unspent:
    print x
    print "---"


raw = bitcoin.createrawtransaction([{"txid":"097162fd9dfe3c85c47c633e639e978b2fb2af6e86527cdc220985a2f6748dcd", "vout":0, "scriptPubKey":"76a914f09cbd5266ac91b347c13a3015a24cba112d0a9988ac", 'sequence':0, 'locktime':1222}], {"mwDZvcxXWNWf9L16FmKWcLSJkpGaYcJaxA":0.09})
print raw

print pprint.pprint(bitcoin.decoderawtransaction(raw))

#bitcoin.signrawtrnsaction(raw, ["cP1f2Cvq2nPoNygg5xq9unb1FB9KmSmAUWpEhzr49aCqwWXyBBMs"])
signed = bitcoin.signrawtransaction(raw)
print signed

#resp = bitcoin.sendrawtransaction(signed['hex'])

