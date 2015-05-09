import hashlib
import mnemonic
import pymongo

import tornado.httpclient
import tornado.escape

from pycoin.key.BIP32Node import BIP32Node

from bitcoin import SelectParams
from bitcoin.core import b2lx, b2x, lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160
from bitcoin.core.script import CScript, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret, CKey
from bitcoin.core.key import CPubKey

SelectParams('testnet')

MONGOCONNECTION = pymongo.Connection('52.1.141.196', 27017)
MONGODB = MONGOCONNECTION.escrow.demo
escrow = MONGODB.find_one({'buyerurlhash':"906618b107da70ed301d701ce8dbff533f35812d"})

phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
seed = mnemonic.Mnemonic.to_seed(phrase)
wallet = BIP32Node.from_master_secret(seed, 'XTN')
toddkeys = []
keys = []
for k in escrow['keys']:
    print k['subkey']
    hdkey = wallet.subkey_for_path(k['subkey'])
    print b2x(CKey(hdkey.sec()).pub)
    print hdkey.sec_as_hex()
    print k['publickey']
    print ""
    toddkeys.append(CKey(hdkey.sec()))
    keys.append(CPubKey(hdkey.address()))


"""
keys = []
for pubkey in escrow['keys']:
    print "PUBLIC KEY", pubkey['publickey']
    keys.append(CPubKey(pubkey['publickey']))
""" 

# Create a redeemScript. Similar to a scriptPubKey the redeemScript must be
# satisfied for the funds to be spent.
redeemScript = CScript(keys)
print(b2x(redeemScript))

# Create the magic P2SH scriptPubKey format from that redeemScript. You should
# look at the CScript.to_p2sh_scriptPubKey() function in bitcoin.core.script to
# understand what's happening, as well as read BIP16:
# https://github.com/bitcoin/bips/blob/master/bip-0016.mediawiki
txin_scriptPubKey = redeemScript.to_p2sh_scriptPubKey()

# Convert the P2SH scriptPubKey to a base58 Bitcoin address and print it.
# You'll need to send some funds to it to create a txout to spend.
txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)

# This is out multi-sig address
print txin_p2sh_address



# Now to sign the transaction
http_client = tornado.httpclient.HTTPClient()
resp = http_client.fetch("https://test-insight.bitpay.com/api/addr/2N2rTBGQScWhVhvEczZuSuudNViT9aM2kw2/utxo")
resp = tornado.escape.json_decode(resp.body)
tx = []
for t in resp:
    txid = t['txid']
    vout = t['vout']
    tx.append({'txid':t['txid'], 'vout':t['vout'], 'scriptPubKey':t['scriptPubKey'], 'amount':t['amount']})


# Create the txin structure, which includes the outpoint. The scriptSig
# defaults to being empty.    
txin = CMutableTxIn(COutPoint(lx(txid), vout))

# Create the txout. This time we create the scriptPubKey from a Bitcoin
# address.
txout = CMutableTxOut(0.0005*COIN, CBitcoinAddress('mmGK3hECmbsCZyAsyH4Dyg9bxir5Ggiid3').to_scriptPubKey())

# Create the unsigned transaction.
tx = CMutableTransaction([txin], [txout])
print "This"
print b2x(tx.serialize())

sighash = SignatureHash(redeemScript, tx, 0, SIGHASH_ALL)

sig = toddkeys[0].sign(sighash) + bytes([SIGHASH_ALL])

txin.scriptSig = CScript([sig, toddkeys[0].pub])


print ""
print(b2x(tx.serialize()))
