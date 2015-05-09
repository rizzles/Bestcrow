import mnemonic

from pycoin.key.BIP32Node import BIP32Node

from pycoin.tx.tx_utils import *
from pycoin.tx import Tx


# variables we'll receive from POST request
tree = [u'0/0/122', u'0/0/123', u'0/0/124']
hex_tx = "010000000116a487e650ea0a55fa7a833b41ef63837da98efa717bbccd1c665c0d1e18f7a70100000000ffffffff01905f0100000000001976a9143f0bd6a98028466602aa347950811e714f7ee76988ac00000000"


# generate wif's
phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
seed = mnemonic.Mnemonic.to_seed(phrase)
# XTN == testnet
wallet = BIP32Node.from_master_secret(seed, 'XTN')

wif = []
for subkey in tree:
    key = wallet.subkey_for_path(subkey)
    wif.append(key.wif())


# sign tx
tx2 = Tx.tx_from_hex(hex_tx)
signed = sign_tx(tx2, wif)
print signed

