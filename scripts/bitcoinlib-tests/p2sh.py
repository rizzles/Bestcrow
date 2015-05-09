from bitcoin.core import b2x, x
from bitcoin.core.script import CScript, IsLowDERSignature
from bitcoin.core.key import CPubKey
from bitcoin.wallet import *


actual_scriptPubKey = addr.to_scriptPubKey()
