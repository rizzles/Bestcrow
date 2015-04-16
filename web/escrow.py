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
from pycoin.encoding import hash160

BITCOIN_RPC_URL = "http://bitcoin:3jf8aAAFh7z7gk22AAd77vhaB788@127.0.0.1:8332"
MONGOCONNECTION = pymongo.Connection('127.0.0.1', 27017)
MONGODB = MONGOCONNECTION.escrow.demo


#import emailer
#from variables import *

clients = {}


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
            (r"/buysell", BuySell),

            (r"/buyer/send/(\w+)", BuyerSend),
            (r"/buyer", Buyer),
            (r"/buyer/(\w+)", Buyer),

            (r"/seller/join/(\w+)", SellerJoin),
            (r"/seller/(\w+)", Seller),

            (r"/recovery", Recovery),
        ]

        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_buyer(self, base58):
        escrow = MONGODB.find_one({'buyerurlhash': str(base58)})
        return escrow

    def get_seller(self, base58):
        escrow = MONGODB.find_one({'sellerurlhash': str(base58)})
        return escrow

    def get_seller_join(self, joinhash):
        escrow = MONGODB.find_one({'joinurlhash': str(joinhash)})
        return escrow

    def update_step3_buyer(self, base58):
        MONGODB.update({"buyerurlhash":base58},{"$set":{"step3":True}})

    def set_seller_address(self, joinhash, selleraddress):
        MONGODB.update({'joinurlhash':joinhash}, {'$set':{'sellerpayoutaddress':selleraddress}})
        trans = MONGODB.find_one({'joinurlhash': str(joinhash)})
        return trans

    def get_balance(self, address):
        http_client = tornado.httpclient.HTTPClient()
        resp = http_client.fetch("http://127.0.0.1:3001/api/addr/%s"%address)
        resp = tornado.escape.json_decode(resp.body)
        print resp
        if resp['unconfirmedBalance'] > 0:
            bal = resp['unconfirmedBalance']
        else:
            bal = resp['balance']
        return bal

    def get_utxo(self, address, sellerhash):
        http_client = tornado.httpclient.HTTPClient()
        resp = http_client.fetch("http://127.0.0.1:3001/api/addr/%s/utxo"%address)
        resp = tornado.escape.json_decode(resp.body)
        info = mongodb.users.find_one({'sellerhash': sellerhash})
        tx = []
        for t in resp:
            tx.append({'txid':t['txid'], 'vout':t['vout'], 'scriptPubKey':t['scriptPubKey']})
        return tx

    # get three pre made mongo keys from the db
    def get_three_keys(self):
        dbkeys = MONGOCONNECTION.escrow.keys.find({'used':False}).limit(3)
        keys = []
        for key in dbkeys:
            MONGOCONNECTION.escrow.keys.update({'publicaddress':key['publicaddress']}, {"$set":{'used':True}})
            keys.append(key)
        return keys

    def make_hash(self):
        # mnemonic phrase for recovery
        m = mnemonic.Mnemonic('english')
        phrase = m.generate()

        # create short hash of phrase
        sha = hashlib.sha256(phrase)
        ripe = hashlib.new("ripemd160", sha.hexdigest())
        ripe = ripe.hexdigest()

        return (ripe, phrase)

    # first step in starting escrow. Setup phrases, we don't complete this until we are given a btc refund address
    def start_escrow(self, buyer=True):
        logging.info('generating mnemonic phrase for new escrow')
        
        buyerhash, buyerphrase = self.make_hash()
        sellerhash, sellerphrase = self.make_hash()
        joinhash = os.urandom(16).encode('hex')

        escrow = {'buyerurlhash': buyerhash,
                  'sellerurlhash': sellerhash,
                  'buyerphrase': buyerphrase,
                  'sellerphrase': sellerphrase,
                  'joinurlhash': joinhash}

        MONGODB.insert(escrow)
        if buyer:
            return buyerhash
        else:
            return sellerhash

    # find the entry in the db that was already started
    def find_started_escrow(self, buyerurlhash=None, sellerurlhash=None):
        if buyerurlhash:
            logging.info("finding already started escrow for buyerurlhash %s"%buyerurlhash)
            escrow = MONGODB.find_one({'buyerurlhash':buyerurlhash})
        else:
            logging.info("finding already started escrow for sellerurlhash %s"%sellerurlhash)
            escrow = MONGODB.find_one({'sellerurlhash':sellerurlhash})
        return escrow

    # final step in the database entry
    @tornado.gen.coroutine
    def create_escrow(self, buyerurlhash=None, sellerurlhash=None, buyeraddress=None, selleraddress=None):
        keys = self.get_three_keys()
        BITCOIN = AsyncAuthServiceProxy(BITCOIN_RPC_URL)

        address1 = keys[0]
        address2 = keys[1]
        address3 = keys[2]

        adds = [address1['publickey'], address2['publickey'], address3['publickey']]
        multiaddress = yield BITCOIN.addmultisigaddress(2, adds)
        redeemscript = yield BITCOIN.createmultisig(2, adds)
        redeemscript = redeemscript['redeemScript']

        if buyerurlhash:
            escrow = self.find_started_escrow(buyerurlhash=buyerurlhash)
        if sellerurlhash:
            escrow = self.find_started_escrow(sellerurlhash=sellerurlhash)

        escrow['keys'] = [address1, address2, address3]
        escrow['sellerpayoutaddress'] = selleraddress
        escrow['buyerpayoutaddress'] = buyeraddress
        escrow['multisigaddress'] = multiaddress
        escrow['multisigbalance'] = 0
        escrow['multitx'] = None
        escrow['step2'] = False
        escrow['step3'] = False
        escrow['buyerstatus'] = 0
        escrow['sellerstatus'] = 1
        
        logging.info("updating new escrow in database with multi sig address = %s"%multiaddress)
        MONGODB.update({'_id':escrow['_id']},{'$set':escrow})
        raise tornado.gen.Return(escrow)


    def get_current_user(self):
        return None
        """
        user = self.get_secure_cookie("btcescrow")
        if not user:
            user = self.get_cookie("btcescrow")
        if not user:
            return None
        user = self.mongodb.users.find_one({'username':user})
        return user
        """

class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")


class Recovery(BaseHandler):
    def get(self):
        self.render('recovery.html', ripe=None)

    def post(self):
        phrase = self.get_argument('phrase', None)

        if phrase:
            sha = hashlib.sha256(phrase)
            ripe = hashlib.new("ripemd160", sha.hexdigest())
            ripe = ripe.hexdigest()
        else:
            ripe = None
        print ripe
        
        self.render('recovery.html', ripe=ripe)


class BuySell(BaseHandler):
    def post(self):
        seller = self.get_argument("buyerseller", None)
        if not seller:
            ripe = self.start_escrow(True)
            self.redirect('/buyer/%s'%ripe)


class BuyerSend(BaseHandler):
    def get(self, base58):
        escrow = self.get_buyer(base58)        
        tx = self.get_utxo(escrow['multisigaddress'], base58)
        amount = escrow['multisigbalance'] - 0.00005
        tx[0]['redeemScript'] = escrow['redeemscript']
        trans = bitcoin.createrawtransaction(tx, {escrow['sellerpayoutaddress']:amount})

        body = {}
        request = tornado.httpclient.HTTPRequest(url=url, method='POST', body=body)
        
        """
        signed1 = bitcoin.signrawtransaction(trans, tx, [escrow['address1privkey']])
        signed2 = bitcoin.signrawtransaction(signed1['hex'], tx, [escrow['address2privkey']])
        multitx = bitcoin.sendrawtransaction(signed2['hex'])
        print multitx
        mongodb.users.update({'buyerhash':base58},{'$set':{'multitx':multitx}})
        """

class Buyer(BaseHandler):
    def get(self, base58):
        escrow = self.get_buyer(base58)
        # unknown hash, redirect to front page
        if not escrow:
            self.redirect("/")
            return
        
        # escrow was started in BuySell class, display first step
        if not escrow.has_key('multisigaddress'):
            self.render('buyerstep1.html', base58=base58, escrow=escrow)
            return

        if not escrow['step3']:
            self.update_step3_buyer(base58)
            self.render('buyerstep3.html', base58=base58, escrow=escrow)
            return
        balance = self.get_balance(escrow['multisigaddress'])
        self.render('buyer.html', base58=base58, escrow=escrow, balance=balance)

    @tornado.gen.coroutine
    def post(self, base58):
        buyeraddress = self.get_argument("buyeraddress", None)
        escrow = self.get_buyer(base58)
        if not escrow.has_key('multisigaddress'):
            # first time we're getting the payout address
            logging.info("first time buyer with public address of %s"%buyeraddress)
            escrow = yield self.create_escrow(buyerurlhash=base58, buyeraddress=buyeraddress)

        self.render('buyerstep2.html', base58=base58, escrow=escrow)
        return


class Seller(BaseHandler):
    def get(self, base58):
        escrow = self.get_seller(base58)
        balance = self.get_balance(escrow['multisigaddress'])
        if not escrow:
            self.write("Sorry, not found. You probably fucked up the URL")
            return
        self.render("seller.html", base58=base58, escrow=escrow, balance=balance)
        

class SellerJoin(BaseHandler):
    def get(self, joinhash):    
        escrow = self.get_seller_join(joinhash)
        self.render("sellerjoin.html", escrow=escrow, joinhash=joinhash)

    def post(self, joinhash):
        address = self.get_argument("selleraddress", None)
        escrow= self.set_seller_address(joinhash, address)
        self.redirect("/seller/%s"%escrow['sellerurlhash'])


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.bind(80)
    http_server.start(1)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 80")

    main()
