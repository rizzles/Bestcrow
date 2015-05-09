import bitcoin
import bitcoin.wallet
import bitcoin.core

import hashlib
import os

bitcoin.SelectParams('testnet')

h = hashlib.sha256('correct horse staple battery').digest()
seckey = bitcoin.wallet.CBitcoinSecret.from_secret_bytes(h)

print seckey
print seckey.pub.is_valid


