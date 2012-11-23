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
import  motor

db=motor.MotorConnection().open_sync().test
application= tornado.web.Application([
    (r"/ask",AskHandler),
    (r"/test",TestHandler),
    (r"/u/(?P<name>.+)/?",PersonalPageHandler),
    (r"/user/settings",UpdateinfoHandler),
    (r"/detail/(?P<detail_id>.+)/?",DetailHandler),
    (r"/tags/?",TagsHandler),
   
    (r"/user/login",LoginHandler),
    (r"/user/register",RegisterHandler),
    (r"/",HomeHandler),
    ],
    db=db,
    template_path=os.path.join(os.path.dirname(__file__),"templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    cookie_secret="bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",

    )
if __name__=="__main__":
    http_server=httpserver.HTTPServer(application)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
