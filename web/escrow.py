import logging
import os
import time
import uuid
import hashlib
import datetime

import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import tornado.escape
import tornado.websocket
import tornado.httpclient

#import emailer
#from variables import *

#walletserver = "ec2-54-82-35-88.compute-1.amazonaws.com:8000"
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
            (r"/buyerstep1", BuyerStep1),
            (r"/buyerstep2", BuyerStep2),
            (r"/buyerstep3", BuyerStep3),   
            (r"/buyer", Buyer),        
        ]


        tornado.web.Application.__init__(self, handlers, **settings)

        #self.mongodb = mongodb

class BaseHandler(tornado.web.RequestHandler):
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

    """
    @property
    def mongodb(self):
        return self.application.mongodb
    """



class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")


class BuySell(BaseHandler):
    def post(self):
        seller = self.get_argument("buyerseller", None)
        if not seller:
            self.redirect('/buyerstep1')


class BuyerStep1(BaseHandler):
    def get(self):
        self.render('buyerstep1.html')


class BuyerStep2(BaseHandler):
    def get(self):
        self.render('buyerstep2.html')


class BuyerStep3(BaseHandler):
    def get(self):
        self.render('buyerstep3.html')


class Buyer(BaseHandler):
    def get(self):
        self.render('buyer.html')


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.bind(80)
    http_server.start(1)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info("Starting web server on port 80")

    main()
