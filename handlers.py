import tornado.web
from tornado import gen
from tornado.options import options as opts

import datetime
import functools
import time 
import re
from models import *
import motor

def check_last_modified(get):
    @functools.wraps(get)
    @tornado.web.asynchronous
    @gen.engine
    def _get(self,*args,**kwargs):
        postdocs =yield motor.Op(self.get_posts,*args,**kwargs)
        print postdocs
        self.posts=posts=[
                Post(**doc) if doc else None
                for doc in postdocs]
        gen.engine(get)(self,*args,**kwargs)
    return _get

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self,**kwargs):
        super(BaseHandler,self).initialize(**kwargs)
        self.db=self.settings["db"]

    def get_template_namespace(self):
        ns= super(BaseHandler,self).get_template_namespace()
        def get_set(setting_name):
            return self.application.settings[setting_name]
        ns.update({"settings":get_set})
        return ns


class HomeHandler(BaseHandler):
    def get_posts(self,callback,page_num=0):
        (self.db.posts.find(
            ).skip(int(page_num)*10)
            .limit(10).to_list(callback))
    
    @tornado.web.addslash
    @check_last_modified
    def get(self,page_num=0):
        print  (self.posts)
        self.render('home.html',
                posts=self.posts)
