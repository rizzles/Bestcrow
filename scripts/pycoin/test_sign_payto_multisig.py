import io
import unittest
import mnemonic

from pycoin.key.BIP32Node import BIP32Node

from pycoin.key import Key
from pycoin.serialize import h2b
from pycoin.tx import Tx, TxIn, TxOut, SIGHASH_ALL, tx_utils
from pycoin.tx.TxOut import standard_tx_out_script

from pycoin.tx.pay_to import ScriptMultisig, ScriptPayToPublicKey
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup, build_p2sh_lookup
from pycoin.tx.pay_to import script_obj_from_address, script_obj_from_script

import pymongo

MONGOCONNECTION = pymongo.Connection('52.1.141.196', 27017)
MONGODB = MONGOCONNECTION.escrow.demo

# get subkeys used for keys out of mongo
escrow = MONGODB.find_one({'buyerurlhash':"906618b107da70ed301d701ce8dbff533f35812d"})
tree = []
for key in escrow['keys']:
    tree.append(key['subkey'])

# generate keys from hd wallet with phrase
phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
seed = mnemonic.Mnemonic.to_seed(phrase)
N, M = 2, 3
wallet = BIP32Node.from_master_secret(seed, 'XTN')
keys = []
for subkey in escrow['keys']:
    key = wallet.subkey_for_path(subkey['subkey'])
    keys.append(key)


tx_in = TxIn.coinbase_tx_in(script=b'')
underlying_script = ScriptMultisig(n=N, sec_keys=[key.sec() for key in keys[:M]]).script()
address = address_for_pay_to_script(underlying_script)
print address
