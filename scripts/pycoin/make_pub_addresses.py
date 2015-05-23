import mnemonic
from pycoin.key.BIP32Node import BIP32Node
import random, binascii, struct, requests
from pycoin.serialize import h2b
import pymongo
from pycoin.encoding import is_hashed_base58_valid
from pycoin.key import Key
from pycoin.serialize import b2h, b2h_rev, h2b, h2b_rev
from pycoin.tx import Tx, TxIn, TxOut, SIGHASH_ALL, tx_utils
from pycoin.tx.TxOut import standard_tx_out_script

from pycoin.tx.pay_to import ScriptMultisig, ScriptPayToPublicKey, ScriptNulldata, ScriptPayToAddress
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup, build_p2sh_lookup
from pycoin.tx.pay_to import script_obj_from_address, script_obj_from_script
from pycoin.key.BIP32Node import BIP32Node
from pycoin.tx.tx_utils import *
from pycoin.tx.script.tools import *

import sys

MONGOCONNECTION = pymongo.MongoClient('127.0.0.1', 27017)
MONGODB = MONGOCONNECTION.escrow.keys
N, M = 2, 3
phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
seed = mnemonic.Mnemonic.to_seed(phrase)

wallet = BIP32Node.from_master_secret(seed)

key = wallet.subkey_for_path("0/0/1")
# public address
print key.address()
# public key
print key.sec_as_hex()
# private key
print key.wif()
# public key in binary
print key.sec()


keys = []
subkeys = []
count = 0
while count < 300:
    subkey = "0/0/%s"%count
    key = wallet.subkey_for_path(subkey)

    keys.append(key)
    subkeys.append(subkey)
    
    if len(keys) == 3:
        redeemscript = ScriptMultisig(n=N, sec_keys=[key.sec() for key in keys[:M]]).script()
        address = address_for_pay_to_script(redeemscript)
        formongo = {'multisigaddress':address, 'used':False, 'subkeys':subkeys}
        MONGODB.insert(formongo)
        keys = []
        subkeys = []

    #if not is_hashed_base58_valid(key.address()):
    #    print "Nope"
    #    sys.exit()

    count += 1

