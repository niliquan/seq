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
    (r"/question/answer",AnswerHandler),
    (r"/test",TestHandler),
    (r"/tagattention",TagAttentionHandler),
    (r"/unfollowtag",UnfollowTagHandler),
    (r"/u/(?P<name>.+)/?",PersonalPageHandler),
    (r"/q/(?P<detail_id>.+)/?",DetailHandler),
    (r"/t/(?P<tagname>.+)/?",TagDetailHandler),
    (r"/tags/?",TagsHandler),
    (r"/page/(?P<page_num>.+)/?",HomeHandler),
    (r"/",HomeHandler),
    (r"/personfollow",PersonFollowHandler),
    (r"/personunfollow",PersonUnfollowHandler),
    #admin
    (r"/user/logout",LogoutHandler),   
    (r"/user/login",LoginHandler),
    (r"/user/register",RegisterHandler),
    (r"/user/settings",UpdateinfoHandler)
    ],
    db=db,
    login_url="/user/login",
    template_path=os.path.join(os.path.dirname(__file__),"templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    cookie_secret="bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
    ui_modules={"User":UserInfoModule,"TagSide":TagModule}
    )
if __name__=="__main__":
    http_server=httpserver.HTTPServer(application)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
