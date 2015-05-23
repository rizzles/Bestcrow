from pycoin.services.insight import InsightService
from pycoin.tx.tx_utils import *
from pycoin.tx import Tx
import pymongo

MONGOCONNECTION = pymongo.Connection('52.1.141.196', 27017)
MONGODB = MONGOCONNECTION.escrow.demo


## Web Server
# convenience method provided by pycoin to get spendables from insight server
insight = InsightService("http://test-insight.bitpay.com")
spendables = insight.spendables_for_address("2MtVnBfNbp4FLbN5XqUcokougUkoVnENRwa")

# create tx from spendables, add in output addresses, and amount
# TODO, need to figure out the 1% we keep for ourselves
# TODO, double check how miner fees are being handled
payables = [("mmGK3hECmbsCZyAsyH4Dyg9bxir5Ggiid3", 1000)]
tx = create_tx(spendables, payables, fee="standard", lock_time=0, version=1)

# this will be the hex of the tx we're going to send in the POST request
hex_tx = tx.as_hex()
print hex_tx

# create tree list of tree strings to send to private key server
escrow = MONGODB.find_one({'buyerurlhash':"7486616f986015614d45136ef16c692e2a7f2b74"})
tree = []
for key in escrow['keys']:
    tree.append(key['subkey'])

print tree


wifs = [u'cNL8fYAZGpWxkvis5qWkgQNyN2pFPbLzoV5aLZWFF2ReowTGvajo', u'cQXwcaACwufruWNzuCPRikWbtTcmLKTT3K2MrA9hYjX8rTJPqtqd', u'cMuhBx2ffDoAQrTLUrnCZsoRe4MWAAETaDTXLSFVDQX2JG1nb3F3']
#print sign_tx(tx, wifs)
create_signed_tx(spendables, payables, wifs)

