import mnemonic
from pycoin.key.BIP32Node import BIP32Node
import random, binascii, struct, requests
from pycoin.serialize import h2b
import pymongo
from pycoin.encoding import is_hashed_base58_valid
import sys

MONGOCONNECTION = pymongo.Connection('127.0.0.1', 27017)
MONGODB = MONGOCONNECTION.escrow.keys

phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
seed = mnemonic.Mnemonic.to_seed(phrase)

wallet = BIP32Node.from_master_secret(seed, 'XTN')

key = wallet.subkey_for_path("0/0/1")
# public address
print key.address()
# public key
print key.sec_as_hex()
# private key
print key.wif()
print key.sec()

sys.exit()

count = 0
while count < 400:
    key = wallet.subkey_for_path("0/0/%s"%count)
    subkey = "0/0/%s"%count

    k = {'publickey':key.sec_as_hex(), 'publicaddress':key.address(), 'used':False, 'subkey':subkey}
    #print k
    #print ""
    print key.address()
    print key.wif()

    """
    if not is_hashed_base58_valid(key.address()):
        print "Nope"
        sys.exit()
    """
    #MONGODB.insert(k)

    count += 1

