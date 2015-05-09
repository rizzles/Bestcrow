from pycoin.key import Key
from pycoin.serialize import h2b
from pycoin.tx import Tx, TxIn, TxOut, SIGHASH_ALL, tx_utils
from pycoin.tx.TxOut import standard_tx_out_script

from pycoin.tx.pay_to import ScriptMultisig, ScriptPayToPublicKey
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup, build_p2sh_lookup
from pycoin.tx.pay_to import script_obj_from_address, script_obj_from_script

import pymongo


MONGOCONNECTION = pymongo.Connection('127.0.0.1', 27017)

keys = MONGOCONNECTION.escrow.keys.find_one({'used':False})


N = 2
M = 3
keys = [Key(secret_exponent=i) for i in range(1, M+2)]
script = ScriptMultisig(2, [Key.from_text(k).sec() for k in sigs.values()])

print script.address()
#print script
