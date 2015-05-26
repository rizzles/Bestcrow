import logging
import os
import time
import uuid
import hashlib
import datetime
import pymongo
import mnemonic
import hashlib

import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import tornado.escape
import tornado.websocket
import tornado.httpclient
import tornado.gen

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from bitcoinrpc_async.authproxy import AsyncAuthServiceProxy, JSONRPCException

from pycoin.key.BIP32Node import BIP32Node

from pycoin.key import Key
from pycoin.serialize import h2b
from pycoin.tx import Tx, TxIn, TxOut, SIGHASH_ALL, tx_utils
from pycoin.tx.TxOut import standard_tx_out_script
from pycoin.tx.tx_utils import *

from pycoin.tx.pay_to import ScriptMultisig, ScriptPayToPublicKey
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup, build_p2sh_lookup
from pycoin.tx.pay_to import script_obj_from_address, script_obj_from_script



BITCOIN_RPC_URL = "http://bitcoin:3jf8aAAFh7z7gk22AAd77vhaB788@127.0.0.1:8332"
PHRASE = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
N, M = 2, 3

class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            cookie_secret="43oETzKXQAGa8Ez82hh9fa3mGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            site_name='escrow',
            xsrf_cookies=False,
            autoescape=None,
            debug=True,
            gzip=True
        )
        handlers = [
            (r"/", MainHandler),
        ]

        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return None


class MainHandler(BaseHandler):
    def post(self):
        logging.info("transaction coming in")
        hextx = self.get_argument('hextx', None)
        subkeys = self.get_argument('subkeys', None)
        payoutaddress = self.get_argument('payoutaddress', None)
        fees = self.get_argument('fees', None)

        print subkeys       

        if not hextx or not subkeys or not payoutaddress or not fees:
            logging.error("Did not receive trans or tree argument")
            return

        fees = tornado.escape.json_decode(fees)        
        subkeys = tornado.escape.json_decode(subkeys)        
        seed = mnemonic.Mnemonic.to_seed(PHRASE)
        wallet = BIP32Node.from_master_secret(seed)

        wifs = []
        keys = []
        for subkey in subkeys:
            key = wallet.subkey_for_path(subkey)
            keys.append(key)
            wifs.append(key.wif())


        underlying_script = ScriptMultisig(n=N, sec_keys=[key.sec() for key in keys[:M]]).script()
        address = address_for_pay_to_script(underlying_script)

        tx2 = Tx.tx_from_hex(hextx)

        # first tx out, need another for the 1% to our wallet
        script = standard_tx_out_script(payoutaddress)
        tx_out = TxOut(fees['seller'], script)
        # TODO: figure out final wallet. This is sending to my phone
        script = standard_tx_out_script("1LhkvTTxFXam672vjwbABtkp9td7dxCwyB")
        tx2_out = TxOut(fees['bestcrow'], script)
        
        txs_out = [tx_out, tx2_out]
        tx2.txs_out = txs_out

        hash160_lookup = build_hash160_lookup(key.secret_exponent() for key in keys)
        p2sh_lookup = build_p2sh_lookup([underlying_script])
        tx2.sign(hash160_lookup=hash160_lookup, p2sh_lookup=p2sh_lookup)

        print tx2.as_hex()
        self.write(tx2.as_hex())

        
def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.bind(8000)
    http_server.start(1)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 8000")

    main()

