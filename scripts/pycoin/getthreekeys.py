import mnemonic
from pycoin.key.BIP32Node import BIP32Node
import random, binascii, struct, requests
from pycoin.serialize import h2b
import pymongo

MONGOCONNECTION = pymongo.Connection('127.0.0.1', 27017)


keys = MONGOCONNECTION.escrow.keys.find({'used':False}).limit(3)

#for key in keys:
#    print key

address1pubaddress = keys[0]['publicaddress']
#MONGOCONNECTION.escrow.keys.remove()
