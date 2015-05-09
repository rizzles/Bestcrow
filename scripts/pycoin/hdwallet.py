import mnemonic
from pycoin.key.BIP32Node import BIP32Node
import random, binascii, struct, requests
from pycoin.serialize import h2b


m = mnemonic.Mnemonic('english')

phrase = m.generate()
print phrase
phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"

seed = mnemonic.Mnemonic.to_seed(phrase)

wallet = BIP32Node.from_master_secret(seed, 'XTN')

path = '%X' % random.randint(0, 2**64-1)


# http://api.greenaddress.it/examples/mnemonic_login.html
while len(path) < 16: path = '0' + path
print path
path_bin = h2b(path)
path_str = '/'.join(str(struct.unpack('!H', path_bin[i*2:(i+1)*2])[0]) for i in xrange(4))
print path_str
wallet_login = wallet.subkey_for_path(path_str)
print wallet_login
subkey = wallet_login


print "PRIVATE", wallet.is_private()
print "PUBLIC X", wallet.public_pair
print "CHILD INDEX", wallet.child_index()
print "WIF",  wallet.wif()

key = wallet.subkey_for_path("0/0/458")
print "SUB KEY WIF", key.wif()
print "SUB KEY ADDRESS", key.address()

key = wallet.subkey_for_path("0/0/459")
print "SUB KEY WIF", key.wif()
print "SUB KEY ADDRESS", key.address()

print wallet_login.secret_exponent
