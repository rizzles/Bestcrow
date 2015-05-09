from pycoin.key import Key
from pycoin.serialize import h2b
from pycoin.tx import Tx, TxIn, TxOut, SIGHASH_ALL, tx_utils
from pycoin.tx.TxOut import standard_tx_out_script

from pycoin.tx.pay_to import ScriptMultisig, ScriptPayToPublicKey
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup, build_p2sh_lookup
from pycoin.tx.pay_to import script_obj_from_address, script_obj_from_script


publicaddress = "mkR94WCqr4gpZauH8ieTLTG6jkZ2uBB6SA"
wif = "cUDx8gXXBZRePmm46LSZetbWqNwXBmm3WQziGVykAgL8NJKMRjQR"


key = Key.from_text(publicaddress)

key = Key(secret_exponent=1)
print key.address()
print key.wif()
print key.secret_exponent()
