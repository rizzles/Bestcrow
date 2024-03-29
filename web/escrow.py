import logging
import os
import time
import uuid
import hashlib
import datetime
import pymongo
import mnemonic
import hashlib
import urllib
import decimal

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

import bitcoinaddress

from pycoin.services.insight import InsightService
from pycoin.tx.tx_utils import *
from pycoin.tx import Tx
from pycoin.key import Key
from pycoin.serialize import h2b
from pycoin.tx import Tx, TxIn, TxOut, SIGHASH_ALL, tx_utils
from pycoin.tx.TxOut import standard_tx_out_script
from pycoin.key.BIP32Node import BIP32Node

from pycoin.tx.pay_to import ScriptMultisig, ScriptPayToPublicKey, ScriptNulldata
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup, build_p2sh_lookup
from pycoin.tx.pay_to import script_obj_from_address, script_obj_from_script
import pycoin.convention

import pymongo


MONGOCONNECTION = pymongo.Connection('54.224.222.213', 27017)
#MONGOCONNECTION = pymongo.MongoClient('localhost', 27017)
MONGODB = MONGOCONNECTION.escrow.demo
MONGOCOMMENTS = MONGOCONNECTION.escrow.democomments
MONGODISPUTE = MONGOCONNECTION.escrow.demodispute
MONGOSUBKEYS = MONGOCONNECTION.escrow.demosubkeys4

INSIGHT = "http://54.224.222.213:3000"
#INSIGHT = "http://localhost:3000"
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
            (r"/buyer/join/(\w+)", BuyerJoin),
            (r"/buyer/receipt/(\w+)", BuyerReceipt),            
            (r"/buyer", Buyer),
            (r"/buyer/(\w+)", Buyer),
            (r"/buyer/dispute/(\w+)", BuyerDispute),

            (r"/seller/join/(\w+)", SellerJoin),
            (r"/seller/(\w+)", Seller),
            (r"/seller/receipt/(\w+)", SellerReceipt),

            (r"/recovery", Recovery),
            (r"/balance/(\w+)", BalanceHandler),
            (r"/comment/(\w+)", CommentHandler),

            (r"/api/join", APIJoinHandler),            
            (r"/api/(\w+)/(\w+)", APIRequestHandler),
            (r"/api/(\w+)", APINewHandler),            
        ]

        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def pretty_date(self, time=False):
        """
        Get a datetime object or a int() Epoch timestamp and return a
        pretty string like 'an hour ago', 'Yesterday', '3 months ago',
        'just now', etc
        """
        now = datetime.datetime.utcnow()
        if type(time) is int:
            diff = now - datetime.datetime.fromtimestamp(time)
        elif isinstance(time, datetime.datetime):
            diff = now - time
        elif not time:
            diff = now - now
        second_diff = diff.seconds
        day_diff = diff.days

        if day_diff < 0:
            return ''

        if day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return str(second_diff) + " seconds ago"
            if second_diff < 120:
                return "a minute ago"
            if second_diff < 3600:
                return str(second_diff / 60) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str(second_diff / 3600) + " hours ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(day_diff) + " days ago"
        if day_diff < 31:
            return str(day_diff / 7) + " weeks ago"
        if day_diff < 365:
            return str(day_diff / 30) + " months ago"
        return str(day_diff / 365) + " years ago"            

    def get_buyer(self, base58):
        escrow = MONGODB.find_one({'buyerurlhash': str(base58)})
        return escrow

    def get_seller(self, base58):
        escrow = MONGODB.find_one({'sellerurlhash': str(base58)})
        return escrow

    def get_joinhash_url(self, joinhash):
        escrow = MONGODB.find_one({'joinurlhash': str(joinhash)})
        return escrow

    def update_step1_buyer(self, base58):
        MONGODB.update({'buyerurlhash':base58},{"$set":{"buyerstep1":True}})

    def update_step1_seller(self, base58):
        MONGODB.update({'sellerurlhash':base58},{"$set":{"sellerstep1":True}})

    def update_step3_buyer(self, base58):
        MONGODB.update({'buyerurlhash':base58},{"$set":{"buyerstep3":True}})

    def set_seller_address(self, joinhash, selleraddress):
        MONGODB.update({'joinurlhash':joinhash}, {'$set':{'sellerpayoutaddress':selleraddress}})
        escrow = MONGODB.find_one({'joinurlhash': str(joinhash)})
        return escrow

    def set_buyer_address(self, joinhash, selleraddress):
        MONGODB.update({'joinurlhash':joinhash}, {'$set':{'buyerpayoutaddress':selleraddress}})
        escrow = MONGODB.find_one({'joinurlhash': str(joinhash)})
        return escrow

    # this is for a escrow that was started in native client and doesn't have a multisig address yet
    # the buyer/seller is joining at this step on the webpage
    def create_multisig(self, escrow):
        logging.info("starting creation of multisig address")
        N, M = 2, 3
        subkeydb = MONGOSUBKEYS.find_one();
        # first time running and we don't have a subkey set in the database
        if not subkeydb:
            subkeydb = MONGOSUBKEYS.insert({'subkey':1});

        # TODO: this has to be moved to the private key server
        # create the first public key. Needed for signing up from the website or the native client.
        subkey = subkeydb['subkey']
        phrase = "sample core fitness wrong unusual inch hurry chaos myself credit welcome margin"
        seed = mnemonic.Mnemonic.to_seed(phrase)
        wallet = BIP32Node.from_master_secret(seed)
        subkeys = []
        keys = []

        if not escrow.has_key('sellerpubky') or not escrow['sellerpubkey']:
            logging.info('seller public key was not provided. We re making and storing the key')
            subkey += 1
            subkeystring = "0/0/"+str(subkey)
            subkeys.append(subkeystring)
            key1 = wallet.subkey_for_path(subkeystring)
        else: 
            logging.info('seller public key was provided from the native client')
            key1 = Key.from_sec(h2b(escrow['sellerpubkey']))
        keys.append(key1)

        if not escrow.has_key('buyerpubkey') or not escrow['buyerpubkey']:
            logging.info('buyer public key was not provided. We re making and storing the key')
            subkey += 1
            subkeystring = "0/0/"+str(subkey)
            subkeys.append(subkeystring)
            key2 = wallet.subkey_for_path(subkeystring)
        else: 
            logging.info('buyer public key was provided from the native client.')
            key2 = Key.from_sec(h2b(escrow['buyerpubkey']))
        keys.append(key2)

        # this is our own, no matter what
        subkey += 1
        subkeystring = "0/0/"+str(subkey)
        subkeys.append(subkeystring)
        key3 = wallet.subkey_for_path(subkeystring)
        keys.append(key3)

        redeemscript = ScriptMultisig(n=N, sec_keys=[key.sec() for key in keys[:M]]).script()
        multisigaddress = address_for_pay_to_script(redeemscript)
        logging.info('multi-sig address was made: %s'%multisigaddress)

        MONGOSUBKEYS.update({'_id':subkeydb['_id']}, {"$set":{'subkey':subkey}}) 
        if escrow.has_key('_id'):
            MONGODB.update({'_id':escrow['_id']}, {"$set":{'multisigaddress': multisigaddress, 'subkeys':subkeys}})
        return (multisigaddress, subkeys)

    def get_balance(self, address):
        http_client = tornado.httpclient.HTTPClient()
        #resp = http_client.fetch("https://test-insight.bitpay.com/api/addr/%s"%address)
        resp = http_client.fetch("%s/api/addr/%s"%(INSIGHT, address))  
        resp = tornado.escape.json_decode(resp.body)
        print resp
        unconfirmed = resp['unconfirmedBalance']
        balance = resp['balance']

        # negative amount still waiting to be confirmed
        if unconfirmed < 0:
            balance += unconfirmed
            if balance == 0:
                balance = 0

        # update balance in db for this address
        return (balance, unconfirmed)

    def get_balance_satoshis(self, address):
        http_client = tornado.httpclient.HTTPClient()
        #resp = http_client.fetch("https://test-insight.bitpay.com/api/addr/%s"%address)
        resp = http_client.fetch("%s/api/addr/%s"%(INSIGHT, address))  
        resp = tornado.escape.json_decode(resp.body)
        print resp
        if resp['unconfirmedBalanceSat'] > 0:
            satoshis = resp['unconfirmedBalanceSat']
        else:
            satoshis = resp['balanceSat']

        fees = self.calc_fees(satoshis)

        return fees

    def calc_fees(self, satoshis):
        logging.info("calculating fee")
        bestcrow = satoshis * 0.01
        logging.info("fee for bestcrow calculated at %s"%bestcrow)
        seller = satoshis - bestcrow
        logging.info("total left for seller after our fee: %s"%seller)

        # calc miners fees to extract from seller price
        miner = 0
        if seller > 10000:
            # this is the recommended fee for btc transactions
            miner = 10000
            seller -= miner
        elif seller > 1000:
            miner = 1000
            seller -= miner
        else:
            miner = 1
            seller -= miner
        logging.info("miners fee: %s"%miner)
        logging.info("total going to seller after miners fee: %s"%seller)
        fees = {'miner':miner, 'seller':seller, 'bestcrow':bestcrow}
        return fees

    def broadcast_transaction(self, tx):
        logging.info("Broadcasting tx to bitcoin network")
        http_client = tornado.httpclient.HTTPClient()
        body = {'rawtx':tx}
        body = urllib.urlencode(body)
        #resp = tornado.httpclient.HTTPRequest("https://test-insight.bitpay.com/api/addr/%s"%address)
        resp = http_client.fetch("%s/api/tx/send"%INSIGHT, method="POST", body=body)
        resp = tornado.escape.json_decode(resp.body)
        logging.info("Send out of escrow account was a success. Txid %s"%resp['txid'])
        return resp['txid']

    def add_dispute(self, dispute):
        logging.info("inserting dispute comment from %s for address %s: %s"%(dispute['author'], dispute['multisigaddress'], dispute['text']))
        MONGODISPUTE.insert({
            'multisigaddress': dispute['multisigaddress'],
            'posted': datetime.datetime.utcnow(),
            'author': dispute['author'],
            'photos': dispute['photos'],
            'text': dispute['text']
        })

    def get_dispute(self, multisigaddress):
        dispute = MONGODISPUTE.find({'multisigaddress': multisigaddress}).sort('posted')
        disputes = []
        for d in dispute:
            d['posted'] = self.pretty_date(d['posted'])
            disputes.append(d)
        return disputes

    def get_comments(self, joinurlhash):
        comments = MONGOCOMMENTS.find({'joinurlhash': joinurlhash}).sort('posted')
        comms = []
        for comment in comments:
            comment['posted'] = self.pretty_date(comment['posted'])
            comms.append(comment)
        return comms

    # get three pre made mongo keys from the db
    def get_multisigaddress(self):
        key = MONGOCONNECTION.escrow.keys.find_one({'used':False})
        MONGOCONNECTION.escrow.keys.update({'multisigaddress':key['multisigaddress']}, {"$set":{'used':True}})
        return key

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
                  'joinurlhash': joinhash,
                  'escrowcomplete': False,
                  'buyerapi': False,
                  'sellerapi': False,
                  'sellerpubkey': None,
                  'buyerpubkey': None,
                  'sellerstep1': False,
                  'buyerstep1': False,
                  'buyerstep3': False,
                  'multisigaddress': None
                }

        MONGODB.insert(escrow)
        if buyer:
            return buyerhash, joinhash
        else:
            return sellerhash, joinhash

    # find the entry in the db that was already started
    def find_started_escrow(self, buyerurlhash=None, sellerurlhash=None):
        if buyerurlhash:
            logging.info("finding already started escrow for buyerurlhash %s"%buyerurlhash)
            escrow = MONGODB.find_one({'buyerurlhash':buyerurlhash})
        else:
            logging.info("finding already started escrow for sellerurlhash %s"%sellerurlhash)
            escrow = MONGODB.find_one({'sellerurlhash':sellerurlhash})
        return escrow

    # final step in the database entry from a signup on the webpage
    def create_escrow(self, buyerurlhash=None, sellerurlhash=None, buyeraddress=None, selleraddress=None):
        N, M = 2, 3
        #key = self.get_multisigaddress()
        escrow = {}
        multisigaddress, subkeys = self.create_multisig(escrow)

        if buyerurlhash:
            escrow = self.find_started_escrow(buyerurlhash=buyerurlhash)
            escrow['buyerstartedescrow'] = 1
            escrow['sellerstartedescrow'] = 0
        if sellerurlhash:
            escrow = self.find_started_escrow(sellerurlhash=sellerurlhash)
            escrow['buyerstartedescrow'] = 0
            escrow['sellerstartedescrow'] = 1

        # pretty sure we don't need to store the redeem script. It can be created again on the key signer server
        escrow['multisigaddress'] = multisigaddress
        escrow['subkeys'] = subkeys
        escrow['sellerpayoutaddress'] = selleraddress
        escrow['buyerpayoutaddress'] = buyeraddress
        escrow['buyerstep3'] = False
        
        logging.info("updating new escrow in database with multi sig address = %s"%escrow['multisigaddress'])
        MONGODB.update({'_id':escrow['_id']},{'$set':escrow})
        return escrow

    def create_api_escrow(self, buyerseller, pubkey):
        N, M = 2, 3
        logging.info('generating mnemonic phrase for new escrow')
        
        buyerhash, buyerphrase = self.make_hash()
        sellerhash, sellerphrase = self.make_hash()
        joinhash = os.urandom(16).encode('hex')

        if buyerseller == 'buyer':
            buyerstartedescrow = 1
            sellerstartedescrow = 0
            buyerpubkey = pubkey
            sellerpubkey = None
            buyerapi = True
            sellerapi = False
        elif buyerseller == 'seller':
            buyerstartedescrow = 0
            sellerstartedescrow = 1
            buyerpubkey = None
            sellerpubkey = pubkey
            buyerapi = False
            sellerapi = True

        escrow = {'buyerurlhash': buyerhash,
                  'sellerurlhash': sellerhash,
                  'buyerphrase': buyerphrase,
                  'sellerphrase': sellerphrase,
                  'joinurlhash': joinhash,
                  'escrowcomplete': False,
                  'buyerapi': buyerapi,
                  'sellerapi': sellerapi,
                  'sellerpubkey': sellerpubkey,
                  'buyerpubkey': buyerpubkey,
                  'buyerstartedescrow': buyerstartedescrow,
                  'sellerstartedescrow': sellerstartedescrow,
                  'sellerstep1': True,
                  'buyerstep1': True,                  
                  'buyerstep3': True,
                  'multisigaddress': None,
                  'sellerpayoutaddress': None,
                  'buyerpayoutaddress': None
                }

        MONGODB.insert(escrow)
        if buyerseller == 'buyer':
            return buyerhash, joinhash
        else:
            return sellerhash, joinhash


    def create_raw_transaction(self, escrow, fees):
        logging.info('starting raw transaction to payout address %s'%escrow['sellerpayoutaddress'])

        # convenience method provided by pycoin to get spendables from insight server
        insight = InsightService(INSIGHT)
        spendables = insight.spendables_for_address(escrow['multisigaddress'])

        # create the tx_in
        txs_in = []
        for s in spendables:
            txs_in.append(s.tx_in())

        script = standard_tx_out_script(escrow['multisigaddress'])

        tx_out = TxOut(fees['seller'], script)
        txs_out = [tx_out]

        tx1 = Tx(version=1, txs_in=txs_in, txs_out=txs_out)
        tx1.set_unspents(txs_out)
        
        # this will be the hex of the tx we're going to send in the POST request
        hex_tx = tx1.as_hex(include_unspents=True)
        
        return hex_tx

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


class BalanceHandler(BaseHandler):
    def get(self, address):
        balance, unconfirmed = self.get_balance(address)
        data = {'balance': balance, 'unconfirmed': unconfirmed}
        data = tornado.escape.json_encode(data)
        self.write(data)


class CommentHandler(BaseHandler):
    def post(self, base58):
        author = self.get_argument("author", None)
        if not author:
            logging.error("no author submitted with comment")
            self.set_status(400)
            return

        if author == 'seller':
            escrow = self.get_seller(base58)
        elif author == 'buyer':
            escrow = self.get_buyer(base58)
        else:
            logging.error("no author submitted with comment")
            self.set_status(400)
            return

        if not escrow:
            logging.error("no escrow found for %s when leaving comment"%base58)
            self.set_status(400)
            return

        comment = self.get_argument("comment", None)

        if not comment:
            logging.error("no comment submitted with comment")
            self.set_status(400)
            return

        MONGOCOMMENTS.insert({
            'multisigaddress': escrow['multisigaddress'],
            'posted': datetime.datetime.utcnow(),
            'author': author,
            'text': comment
            })

        logging.info("comment: %s : left by %s"%(comment, author))

        self.set_status(200)
        self.write("from server")


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
        self.render('recovery.html', ripe=ripe)


class BuySell(BaseHandler):
    def post(self):
        seller = self.get_argument("buyerseller", None)
        if not seller:
            ripe, joinhash = self.start_escrow(buyer=True)
            self.redirect('/buyer/%s'%ripe)
        else:
            ripe, joinhash = self.start_escrow(buyer=False)
            self.redirect('/seller/%s'%ripe)


class BuyerSend(BaseHandler):
    def get(self, base58):
        escrow = self.get_buyer(base58)
        fees = self.get_balance_satoshis(escrow['multisigaddress'])
        MONGODB.update({'_id':escrow['_id']},{'$set':{'fees':fees}})        
        hextx  = self.create_raw_transaction(escrow, fees)

        body = urllib.urlencode({'hextx':hextx, 'subkeys':tornado.escape.json_encode(escrow['subkeys']), 'payoutaddress':escrow['sellerpayoutaddress'], 'fees':tornado.escape.json_encode(fees)})

        http_client = tornado.httpclient.HTTPClient()
        try:
            result = http_client.fetch("http://127.0.0.1:8000", method="POST", body=body)
        except Exception, e:
            logging.error("Communication with private key server error: %s"%e)
            return

        txid = self.broadcast_transaction(result.body)
        MONGODB.update({'_id':escrow['_id']}, {"$set": {"transactionid":txid, "transactiontime":datetime.datetime.utcnow(), "escrowcomplete": True}})
        self.redirect("/buyer/receipt/%s"%base58)


class BuyerReceipt(BaseHandler):
    def get(self, base58):
        escrow = self.get_buyer(base58)
        balance, unconfirmed = self.get_balance(escrow['multisigaddress'])
        self.render("buyerreceipt.html", escrow=escrow, balance=balance, unconfirmed=unconfirmed, satoshi_to_btc=pycoin.convention.satoshi_to_btc, decimal=decimal)


class BuyerDispute(BaseHandler):
    def post(self, base58):
        escrow = self.get_buyer(base58)
        description = self.get_argument("description", None)
        photos = self.request.files

        if not photos and not description:
            logging.error("No description of photos submitted with dispute")
            self.redirect("/buyer/%s"%escrow['buyerurlhash'])
            return

        p = []
        if photos.has_key('photo'):
            for photo in photos['photo']:
                filename = photo['filename']
                content_type = photo['content_type']
                file_body = photo['body']
                p.append({'filename':filename, 'content_type':content_type})
                logging.info("buyer %s uploaded photo %s"%(escrow['buyerurlhash'], filename))
                if not os.path.exists("dispute/%s"%escrow['multisigaddress']):
                    os.makedirs("dispute/%s"%escrow['multisigaddress'])
                f = open("dispute/%s/%s"%(escrow['multisigaddress'], filename), 'w+')
                f.write(file_body)
                f.close()

        dispute = {}
        if p:
            dispute['photos'] = p
        else:
            dispute['photos'] = None

        if description:
            dispute['text'] = description
        else:
            dispute['text'] = None
        
        dispute['author'] = 'buyer'
        dispute['multisigaddress'] = escrow['multisigaddress']
        self.add_dispute(dispute)

        self.redirect("/buyer/%s"%escrow['buyerurlhash'])


class Buyer(BaseHandler):
    def get(self, base58):
        escrow = self.get_buyer(base58)
        # unknown hash, redirect to front page
        if not escrow:
            self.redirect("/")
            return
        
        # escrow was started in BuySell class, display first step
        if not escrow['buyerstep1']:
            self.update_step1_buyer(base58)
            self.render('buyerstep1.html', base58=base58, escrow=escrow, errors=None)
            return

        if not escrow['buyerstep3']:
            self.update_step3_buyer(base58)
            self.render('buyerstep3.html', base58=base58, escrow=escrow)
            return

        comments = self.get_comments(escrow['joinurlhash'])
        dispute = self.get_dispute(escrow['joinurlhash'])

        if escrow['multisigaddress']:
            balance, unconfirmed = self.get_balance(escrow['multisigaddress'])
        else:
            balance = 0
            unconfirmed = 0

        self.render('buyer.html', base58=base58, escrow=escrow, balance=balance, unconfirmed=unconfirmed, comments=comments, satoshi_to_btc=pycoin.convention.satoshi_to_btc, decimal=decimal, dispute=dispute)

    def post(self, base58):
        buyeraddress = self.get_argument("buyeraddress", None)
        escrow = self.get_buyer(base58)

        if not bitcoinaddress.validate(buyeraddress):
            logging.error("an invalid bitcoin address was submitted by the buyer on signup. Address: %s"%buyeraddress)
            self.render('buyerstep1.html', base58=base58, escrow=escrow, errors="invalid")
            return

        if not escrow.has_key('multisigaddress') or not escrow['multisigaddress']:
            # first time we're getting the payout address
            logging.info("first time buyer with public address of %s"%buyeraddress)
            escrow = self.create_escrow(buyerurlhash=base58, buyeraddress=buyeraddress)

        self.render('buyerstep2.html', base58=base58, escrow=escrow)
        return


class BuyerJoin(BaseHandler):
    def get(self, joinhash):
        escrow = self.get_joinhash_url(joinhash)
        self.render("buyerjoin.html", escrow=escrow, joinhash=joinhash, errors=None)

    def post(self, joinhash):
        address = self.get_argument("buyeraddress", None)
        escrow = self.get_joinhash_url(joinhash)

        if not bitcoinaddress.validate(address):
            logging.error("an invalid bitcoin address was submitted by the buyer on joining. Address: %s"%address)
            self.render('buyerjoin.html', joinhash=joinhash, escrow=escrow, errors="invalid")
            return

        # create multi sig address if we don't have one because escrow was started in native client
        if not escrow['multisigaddress']:
            self.create_multisig(escrow)

        escrow = self.set_buyer_address(joinhash, address)
        self.update_step3_buyer(escrow['buyerurlhash'])

        self.redirect("/buyer/%s"%escrow['buyerurlhash'])


class Seller(BaseHandler):
    def get(self, base58):
        escrow = self.get_seller(base58)
        # unknown hash, redirect to the front page
        if not escrow:
            self.redirect("/")
            return

        # escrow was just started, display first step
        if not escrow['sellerstep1']:
            self.render('sellerstep1.html', base58=base58, escrow=escrow, errors=None)
            return

        comments = self.get_comments(escrow['joinurlhash'])
        dispute = self.get_dispute(escrow['joinurlhash'])

        if escrow['multisigaddress']:
            balance, unconfirmed = self.get_balance(escrow['multisigaddress'])
        else:
            balance = 0
            unconfirmed = 0
        
        self.render("seller.html", base58=base58, escrow=escrow, balance=balance, unconfirmed=unconfirmed, comments=comments, satoshi_to_btc=pycoin.convention.satoshi_to_btc, decimal=decimal, dispute=dispute)
        
    def post(self, base58):
        selleraddress = self.get_argument("selleraddress", None)
        escrow = self.get_seller(base58)

        if not bitcoinaddress.validate(selleraddress):
            logging.error("an invalid bitcoin address was submitted by the seller on signup. Address: %s"%selleraddress)
            self.render('sellerstep1.html', base58=base58, escrow=escrow, errors="invalid")
            return

        if not escrow.has_key('multisigaddress') or not escrow['multisigaddress']:
            # first time we're getting the seller payout address
            logging.info("first time seller with public address of %s"%selleraddress)
            escrow = self.create_escrow(sellerurlhash=base58, selleraddress=selleraddress)

        self.render('sellerstep2.html', base58=base58, escrow=escrow)
        return


class SellerReceipt(BaseHandler):
    def get(self, base58):
        escrow = self.get_seller(base58)
        balance, unconfirmed = self.get_balance(escrow['multisigaddress'])
        self.render("sellerreceipt.html", escrow=escrow, balance=balance, unconfirmed=unconfirmed, satoshi_to_btc=pycoin.convention.satoshi_to_btc, decimal=decimal)


class SellerJoin(BaseHandler):
    def get(self, joinhash):
        escrow = self.get_joinhash_url(joinhash)
        self.render("sellerjoin.html", escrow=escrow, joinhash=joinhash, errors=None)

    def post(self, joinhash):
        address = self.get_argument("selleraddress", None)
        escrow = self.get_joinhash_url(joinhash)

        if not bitcoinaddress.validate(address):
            logging.error("an invalid bitcoin address was submitted by the seller on signup. Address: %s"%address)
            self.render('sellerjoin.html', joinhash=joinhash, escrow=escrow, errors="invalid")
            return

        # create multi sig address if we don't have one because escrow was started in native client
        if not escrow.has_key('multisigaddress') or not escrow['multisigaddress']:
            self.create_multisig(escrow)

        escrow = self.set_seller_address(joinhash, address)
        self.update_step1_seller(escrow['sellerurlhash'])
        self.redirect("/seller/%s"%escrow['sellerurlhash'])


class APINewHandler(BaseHandler):
    # this is first time request coming in from native client to start new escrow
    def post(self, buyerseller):  
        logging.info("Starting new escrow api call being made")
        data = tornado.escape.json_decode(self.request.body)
        pubkey = data['pubKey']
        buyerseller = data['buyerSeller']

        if buyerseller == 'buyer':
            buyer = True
        elif buyerseller == 'seller':
            buyer = False   

        escrowhash, joinhash = self.create_api_escrow(buyerseller, pubkey)
        data = {'escrowhash': escrowhash, 'joinhash':joinhash}
        self.write(tornado.escape.json_encode(data))


class APIRequestHandler(BaseHandler):
    def put(self, buyerseller, base58):
        print self.request.body

    # just a get request to find latest db data
    def get(self, buyerseller, base58):
        logging.info("API request coming in")
        if buyerseller == 'buyer':
            escrow = self.get_buyer(base58) 
            escrow.pop("sellerurlhash", None)
        elif buyerseller == 'seller':
            escrow = self.get_seller(base58)
            escrow.pop("buyerurlhash", None)                    
        else: 
            logging.error("Bad API request")
            return

        escrow.pop("_id", None)  
        escrow.pop("buyerphrase", None)          
        escrow.pop("sellerphrase", None)
        print escrow['multisigaddress']
        if escrow['multisigaddress']:
            escrow['balance'], escrow['unconfirmed'] = self.get_balance(escrow['multisigaddress'])                
        else:
            escrow['balance'] = 0
            escrow['unconfirmed'] = 0

        self.write(tornado.escape.json_encode(escrow))


class APIJoinHandler(BaseHandler):
    def post(self):
        logging.info('Join API request to join an existing escrow')
        data = tornado.escape.json_decode(self.request.body)
        pubkey = data['pubKey']
        joinhash = data['joinHash'] 
        buyerSeller = data['buyerSeller']
        pubKey = data['pubKey']

        escrow = self.get_joinhash_url(joinhash);

        # TODO: Have to figure out how to get the buyer/seller payout address from native client
        # probably going to do something on first boot of native client
        if buyerSeller == 'buyer':
            escrow['buyerpubkey'] = pubKey
            escrow['buyerapi'] = True
            # Change this for the payout address
            escrow['buyerpayoutaddress'] = pubKey
            escrowhash = escrow['buyerurlhash']
        else:
            escrow['sellerpubkey'] = pubKey
            escrow['sellerapi'] = True
            # Change this for the payout address            
            escrow['sellerpayoutaddress'] = True
            escrowhash = escrow['sellerurlhash']               

        if not escrow['multisigaddress']:
            escrow['multisigaddress'], escrow['subkeys'] = self.create_multisig(escrow)

        print escrow['multisigaddress']

        MONGODB.update({'_id':escrow['_id']},{'$set':escrow})
        data = {'multisigaddress': escrow['multisigaddress'], 'escrowhash':escrowhash}
        print data
        self.write(tornado.escape.json_encode(data))


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.bind(80)
    http_server.start(1)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 80")

    main()
