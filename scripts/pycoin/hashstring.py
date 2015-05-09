import mnemonic
from pycoin.key.BIP32Node import BIP32Node
import random, binascii, struct, requests
from pycoin.serialize import h2b
import hashlib

m = mnemonic.Mnemonic('english')

"""
phrase = m.generate()
print phrase
"""
phrase = "knock much brief flash pair seven flat life clever innocent arrange sleep"
print phrase

h = hashlib.sha256(phrase)
sha =  h.hexdigest()
print sha

ripe = hashlib.new("ripemd160", sha)
print ripe.hexdigest()
