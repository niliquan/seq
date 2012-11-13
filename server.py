import os
import logging
import sys

import pytz
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.web import StaticFileHandler
from tornado import httpserver
from  handlers import *
import motor

db=motor.MotorConnection().open_sync().test
application= tornado.web.Application([
    (r"/",HomeHandler)
    ],
    db=db,
    template_path=os.path.join(os.path.dirname(__file__),"templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
if __name__=="__main__":
    http_server=httpserver.HTTPServer(application)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
