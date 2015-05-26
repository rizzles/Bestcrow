#!/usr/bin/env python

import mnemonic

import io
import unittest

from pycoin.key import Key
from pycoin.serialize import b2h, b2h_rev, h2b, h2b_rev
from pycoin.tx import Tx, TxIn, TxOut, SIGHASH_ALL, tx_utils
from pycoin.tx.TxOut import standard_tx_out_script

from pycoin.tx.pay_to import ScriptMultisig, ScriptPayToPublicKey, ScriptNulldata, ScriptPayToAddress
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup, build_p2sh_lookup
from pycoin.tx.pay_to import script_obj_from_address, script_obj_from_script
from pycoin.key.BIP32Node import BIP32Node
from pycoin.tx.tx_utils import *
from pycoin.services.insight import InsightService
from pycoin.convention import tx_fee


insight = InsightService("http://localhost:3000")

pubkeys = ["mhmXxis5TNfYjSjsyVZbwB7Vdcphe9kzZ7", "mxfaexGi4r3zFoekTPRytpadPCfrHiv9gb", "mvu1Srmr16sFsTuw1VW7xKnmjWr2XJQSMk"]
phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
subkeys = ["0/0/138", "0/0/139", "0/0/140"]
wifs = []



seed = mnemonic.Mnemonic.to_seed(phrase)
wallet = BIP32Node.from_master_secret(seed)
for subkey in subkeys:
    key = wallet.subkey_for_path(subkey)
    wifs.append(key.wif())




N, M = 2, 3
## TODO: create private keys. This is using wifs. Need to use only pub keys
keys = [Key.from_text(wifs[i]) for i in range(0, M)]

# redeem script. Sets it as 2-of-3. The hash of this is the bitcoin address 
underlying_script = ScriptMultisig(n=N, sec_keys=[key.sec() for key in keys[:M]]).script()

# multisig address. Just hash the redeem script
address = address_for_pay_to_script(underlying_script)





## going to create a spend from this address. This should be the code on the web server
spendables = insight.spendables_for_address(address)
txs_in = []
for s in spendables:
    print s
    txs_in.append(s.tx_in())




# make tx_out on web server
script = standard_tx_out_script(address)
tx_out = TxOut(100000, script)
txs_out = [tx_out]

tx1 = Tx(version=1, txs_in=txs_in, txs_out=txs_out)
tx1.set_unspents(txs_out)

txhex = tx1.as_hex(include_unspents=True)



# send txhex to private key server
tx2 = Tx.tx_from_hex(txhex)
script = standard_tx_out_script("1F8P3QEErMhm3fw6o23brRNQVaSMrG1maE")
tx_out = TxOut(50000, script)
script = standard_tx_out_script("1Dv9YWfVYMK1FjBhrCBc1diajSZKBj78MB")
tx2_out = TxOut(50000, script)

txs_out = [tx_out, tx2_out]
tx2.txs_out = txs_out



hash160_lookup = build_hash160_lookup(key.secret_exponent() for key in keys[:M])
p2sh_lookup = build_p2sh_lookup([underlying_script])

tx2.sign(hash160_lookup=hash160_lookup, p2sh_lookup=p2sh_lookup)
print tx2.as_hex()


