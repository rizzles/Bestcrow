from bitcoin import *

from pycoin.key.BIP32Node import BIP32Node

import hashlib
import mnemonic
import pymongo

import tornado.httpclient
import tornado.escape
import urllib

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException


MONGOCONNECTION = pymongo.Connection('52.1.141.196', 27017)
MONGODB = MONGOCONNECTION.escrow.demo
BITCOIN_RPC_URL = "http://bitcoin:3jf8aAAFh7z7gk22AAd77vhaB788@127.0.0.1:8332"
escrow = MONGODB.find_one({'buyerurlhash':"f9098f8011440d3684da63745805cf5c101b00cd"})


## Create redeemscript and multi-sig address
key1 = escrow['keys'][0]['publickey']
key2 = escrow['keys'][1]['publickey']
key3 = escrow['keys'][2]['publickey']
print key1, key2, key3
redeemscript = mk_multisig_script(key1, key2, key3, 2, 3)
multisigaddress = scriptaddr(redeemscript)


# get private keys from subkey of hd wallet
phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
seed = mnemonic.Mnemonic.to_seed(phrase)
wallet = BIP32Node.from_master_secret(seed, 'XTN')
privkeys = []
for k in escrow['keys']:
    hdkey = wallet.subkey_for_path(k['subkey'])
    privkeys.append(hdkey.wif())




# Get the unspents from insight
http_client = tornado.httpclient.HTTPClient()
resp = http_client.fetch("https://test-insight.bitpay.com/api/addr/%s/utxo"%escrow['multisigaddress'])
resp = tornado.escape.json_decode(resp.body)
unspent = []
for t in resp:
    print t
    unspent.append({'txid':t['txid'], 'vout':t['vout'], 'scriptPubKey':t['scriptPubKey'], 'amount':t['amount']})



# Create the tx with unputs and outputs
input = ["%s:%s"%(unspent[0]['txid'],unspent[0]['vout'])]
output = ["mz8p8gHyAWbi7ervPk7KoaBX8pGxXXeSXW:10000"]
tx = mktx(input, output)
print ""
print "TX1", tx



# sign the transaction
sig1 = multisign(tx, 0, str(escrow['redeemscript']), privkeys[0])
sig2 = multisign(tx, 0, str(escrow['redeemscript']), privkeys[1])
tx2 = apply_multisignatures(tx, 0, str(escrow['redeemscript']), sig1, sig2)

print ""
print "TX2", tx2
print ""



"""
# Send that shit
http_client = tornado.httpclient.HTTPClient()
body =  urllib.urlencode({'rawtx':tx2})
try:
    resp = http_client.fetch("http://test-insight.bitpay.com/api/tx/send", method="POST", body=body)
except Exception, e:
    print "ERROR", e
"""

"""
conn = AuthServiceProxy(BITCOIN_RPC_URL)
try:
    conn.sendrawtransaction(tx2)
except JSONRPCException, e:
    print "ERROR:", e.error
"""
