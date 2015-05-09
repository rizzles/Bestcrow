#!/usr/bin/python

import os.path
import re
import sys
import logging
import datetime
import base64
import time
import uuid
import random
import pymongo

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.options
import tornado.locale
import tornado.websocket

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

import requests

bitcoin = AuthServiceProxy("http://bitcoin:3jf8aAAFh7z7gk22AAd77vhaB788@127.0.0.1:8332")
mikes = "mgsUnLsMhphUyFiiCDBa6UWqhDivWaNwSe"
mine = "mpbJSfca2Z5vwB5ogMhPTJ3DBx2fZDMkGz"
pubkeymike = "03985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d"
pubkeymine = "03133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df061"
multiaddress = "2NC9uL5Qcnt4awdTBi3jB6ADPVdvwP9iR8L"
redeemscript = "522103133255e240ded2cd1d0b8fa5b659fd7713b74f6ea074f4a80e3cb1f0677df0612103985457b91195038af91c1c7b09c693e9a141681319b683c46871b2dbf1beb09d52ae"

random = "mrTRKLaDF86gLdKnacjxkXJdRFS6S8poTY"
txtorandom = "bdad390ea15f1828466266a97d4f219ff2e64111a60cb204b30148b199260bd0"
random2 = "mmQDjcub4ozy7e7ET6Yx75MDcLQHdhofbU"

hashes = {}

mongoconnection = pymongo.Connection('127.0.0.1', 27017)
mongodb = mongoconnection.escrow


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/setupmultiwallet", SetupMultiWallet),

            (r"/buyer/getstarted", BuyerGetStarted),
            (r"/seller/getstarted", SellerGetStarted),

            (r"/seller/join/(\w+)", SellerJoin),
            (r"/buyer/join/(\w+)", BuyerJoin),

            (r"/buyer/(\w+)", BuyerHandler),
            (r"/seller/(\w+)", SellerHandler),
            ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
            cookie_secret="92oP7zKYxAB4YGkL3gUmGerJFuYh7EQnp3XdTP1oxco=",
            site_name='itchycats',
            login_url='/',
            autoescape=None,
            debug=True,
            gzip=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def get_info(self, hashest):
        mongodb.users.find({'hashest': hashest})

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

    """
    @property
    def get_current_user(self):
        return None
    """

class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")


class SetupMultiWallet(BaseHandler):
    def post(self):
        buyeraddress = self.get_argument('buyeraddress', None)
        selleraddress = self.get_argument('selleraddress', None)
        
        address1pubaddress = bitcoin.getnewaddress("")
        address1pubkey = bitcoin.validateaddress(address1pubaddress)['pubkey']
        address1privkey = bitcoin.dumpprivkey(address1pubaddress)

        address2pubaddress = bitcoin.getnewaddress("")
        address2pubkey = bitcoin.validateaddress(address2pubaddress)['pubkey']
        address2privkey = bitcoin.dumpprivkey(address2pubaddress)

        address3pubaddress = bitcoin.getnewaddress("")
        address3pubkey = bitcoin.validateaddress(address3pubaddress)['pubkey']
        address3privkey = bitcoin.dumpprivkey(address3pubaddress)

        adds = [address1pubkey, address2pubkey, address3pubkey]
        multiaddress = bitcoin.addmultisigaddress(2, adds)
        redeemscript = bitcoin.createmultisig(2, adds)
        redeemscript = redeemscript['redeemScript']

        buyerhash = os.urandom(16).encode('hex')
        sellerhash = os.urandom(16).encode('hex')
        joinhash = os.urandom(16).encode('hex')
        info = {'buyerhash': buyerhash,
                'sellerhash': sellerhash,
                'joinhash': joinhash,

                'sellerpayoutaddress': selleraddress,
                'buyerpayoutaddress': buyeraddress,

                'multisigaddress': multiaddress,
                'multisigbalance': 0,
                'multitx': None,

                'address1pubkey': address1pubkey,
                'address1privkey': address1privkey,
                'address1pubaddress': address1pubaddress,
                'address2pubkey': address2pubkey,
                'address2privkey': address2privkey,
                'address2pubaddress': address2pubaddress,
                'address3pubkey': address3pubkey,
                'address3privkey': address3privkey,
                'address3pubaddress': address3pubaddress,
                'redeemscript': redeemscript,

                'buyerstatus': 0,
                'sellerstatus': 1,
                }
        
        mongodb.users.insert(info)

        if selleraddress:
            self.redirect("/seller/%s"%sellerhash)
        else:
            self.redirect("/buyer/%s"%buyerhash)


class SellerGetStarted(BaseHandler):
    def get(self):
        self.render('sellergetstarted.html')


class BuyerGetStarted(BaseHandler):
    def get(self):
        self.render('buyergetstarted.html')


class SellerJoin(BaseHandler):
    def get(self, joinhash):
        info = mongodb.users.find_one({'joinhash': joinhash})
        self.render("sellerjoin.html", joinhash=joinhash, info=info)

    def post(self, joinhash):
        address = self.get_argument("address", None)
        mongodb.users.update({'joinhash':joinhash}, {'$set':{'sellerpayoutaddress':address}})
        info = mongodb.users.find_one({'joinhash': joinhash})
        self.redirect("/seller/%s"%info['sellerhash'])


class BuyerJoin(BaseHandler):
    def get(self, joinhash):
        info = mongodb.users.find_one({'joinhash': joinhash})
        self.render("buyerjoin.html", joinhash=joinhash, info=info)

    def post(self, joinhash):
        address = self.get_argument("address", None)
        mongodb.users.update({'joinhash':joinhash}, {'$set':{'buyerpayoutaddress':address}})
        info = mongodb.users.find_one({'joinhash': joinhash})
        self.redirect("/buyer/%s"%info['buyerhash'])


class BuyerHandler(BaseHandler):
    def get(self, buyerhash):
        info = mongodb.users.find_one({'buyerhash': buyerhash})
        balance = self.get_balance(info['multisigaddress'])

        mongodb.users.update({'buyerhash':buyerhash},{'$set':{'multisigbalance':float(balance)}})
        self.render("buyer.html", info=info, balance=balance)

    def post(self, buyerhash):
        info = mongodb.users.find_one({'buyerhash': buyerhash})
        if info['sellerstatus']:
            mongodb.users.update({'buyerhash':buyerhash},{'$set':{'buyerstatus':1}})
        tx = self.get_utxo(info['multisigaddress'], buyerhash)
        amount = info['multisigbalance'] - 0.00005
        tx[0]['redeemScript'] = info['redeemscript']
        trans = bitcoin.createrawtransaction(tx, {info['sellerpayoutaddress']:amount})
        signed1 = bitcoin.signrawtransaction(trans, tx, [info['address1privkey']])
        signed2 = bitcoin.signrawtransaction(signed1['hex'], tx, [info['address2privkey']])
        multitx = bitcoin.sendrawtransaction(signed2['hex'])
        print multitx
        mongodb.users.update({'buyerhash':buyerhash},{'$set':{'multitx':multitx}})

        self.redirect("/buyer/%s"%buyerhash)
        
    
class SellerHandler(BaseHandler):
    def get(self, sellerhash):
        info = mongodb.users.find_one({'sellerhash': sellerhash})
        balance = self.get_balance(info['multisigaddress'])

        mongodb.users.update({'sellerhash':sellerhash},{'$set':{'multisigbalance':float(balance)}})
        self.render("seller.html", info=info, balance=balance)

    def post(self, sellerhash):
        sellerhash = self.get_argument("sellerhash", None)
        mongodb.users.update({'sellerhash':sellerhash},{'$set':{'sellerstatus':1}})
        
        self.redirect("/seller/%s"%sellerhash)


class GetSellerAddress(BaseHandler):
    def get(self):
        address = self.get_arguemnt("address", None)
        sellerhash = self.get_argument("sellerhash", None)
        

def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(80)
    tornado.ioloop.IOLoop.instance().start()
    logging.info("Escrow web server started successfully")

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting escrow web server")

    main()
