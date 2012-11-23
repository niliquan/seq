# -*- coding:utf-8 -*-
import tornado.web
from tornado import gen
from tornado.options import options as opts
from bson.objectid import ObjectId
import datetime
import functools
import time 
import re
from models import *
import motor
import Image
import tempfile

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
    def get_current_user(self):
        return self.get_secure_cookie("name")

    def initialize(self,**kwargs):
        super(BaseHandler,self).initialize(**kwargs)
        self.db=self.settings["db"]

    def get_template_namespace(self):
        ns= super(BaseHandler,self).get_template_namespace()
        def get_set(setting_name):
            return self.application.settings[setting_name]
        ns.update({"settings":get_set})
        return ns


class DetailHandler(BaseHandler):
  
    @tornado.web.addslash
    @tornado.web.asynchronous
    @gen.engine
    def get(self,detail_id):
        detail_id=detail_id.rstrip("/")
        posts=self.db.posts
        postdoc=yield motor.Op(posts.find_one,{"_id":ObjectId(detail_id)})
        
        if not postdoc:
            raise tornado.web.HTTPError(404)

        postdoc=Post(**postdoc)
        print postdoc.title
        self.render("detail.html",post=postdoc)


class HomeHandler(BaseHandler):

    def get_posts(self,callback,page_num=0):
        (self.db.posts.find(
            ).skip(int(page_num)*10)
            .limit(10).to_list(callback))
    
    @tornado.web.addslash
    @check_last_modified
    def get(self,page_num=0):
        email=self.get_secure_cookie("email")
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if userinfo:
            userinfo=User(**userinfo)
        self.render('home.html',
                posts=self.posts,userinfo=userinfo)
  

class UpdateinfoHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        email=self.get_secure_cookie("email")
        if not email:
            self.redirect("/user/login")
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if not userinfo:
            self.redirect("/user/login")
        print userinfo
        userinfo=User(**userinfo)
        self.render("addinfo.html",userinfo=userinfo)

    @tornado.web.asynchronous
    @gen.engine
    def post(self):
        #查找一个用户记录
        print "1"
        email=self.get_secure_cookie("email")
        print "2"
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if not email and not  userinfo:
            self.redirect("/")
            return
        print "wrong"
     #   userinfo=User(**userinfo)
     #   print userinfo
        id=userinfo["_id"]
        userinfo.update({
            "name":self.get_argument("name"),
            "address":self.get_argument("address"),
            "homepage":self.get_argument("homepage"),
            "birthday":self.get_argument("birthday"),
            "description":self.get_argument("description")})

#上传图片
        if not self.request.files:
            self.write("<script>alert('no picture')</script>")
            self.finish()
            return
        send_file=self.request.files["avatar"][0]
        print send_file["filename"]
        tmp_file=tempfile.NamedTemporaryFile(delete=True)
        tmp_file.write(send_file["body"])
        tmp_file.seek(0)
        try:
            image_one=Image.open(tmp_file.name)
        except IOError,error:
            self.write('<script>alert"illegal"</script>')

        image_path="./static/pic/"
        image_format=send_file["filename"]
        storename="pic/"+ str(int(time.time()))+image_format
        tmp_name="./static/"+storename
#        tmp_name=image_path+str(int(time.time()))+image_format
        image_one.save(tmp_name)
        
        tmp_file.close()
        userinfo.update({"pic_url":storename})

#修改用户数据
        user_id=yield motor.Op(self.db.users.update,{"_id":id},userinfo)
        self.set_secure_cookie("name",self.get_arugument("name"))
        self.finish()


class TestHandler(BaseHandler):

    def get(self):
        self.render("test.html")
    
    def post(self):
        print "in method"
        name=self.get_argument("name")
        print name
        self.write(name)
        return




class LoginHandler(BaseHandler):

    def get(self):
        if self.current_user:
            self.redirect("/")
        else:
            self.render('login.html')

    @tornado.web.asynchronous
    @gen.engine
    def post(self):
        email = self.get_argument("email")
        password=self.get_argument("password")
        if (not email) and (not password):
            self.write(" 请输入完整登录信息 ")
            return 
        userinfo =yield motor.Op(self.db.users.find_one,{"email":email})
        if not  userinfo:
            self.redirect("/login")
            self.finsh()
            return
        else:
            user_find=User(**userinfo)
            if user_find.password == password and user_find.email == email:
                self.set_secure_cookie("name",user_find.name)
                self.set_secure_cookie("email",user_find.email)
                self.redirect("/")
                return 
            else :
                self.redirect("/user/login")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect("/")

    def post(self):
        self.clear_all_cookies()
        self.redirect("/")

class RegisterHandler(BaseHandler):
    
    def get(self):
        self.clear_cookie("email")
        self.render("register.html")
    
    @tornado.web.asynchronous
    @gen.engine
    def post(self):
        user={}
        email=self.get_argument("email")
        password=self.get_argument("password")
        name=self.get_argument("name")
        if (not name) and (not password) and (not email):
            self.write("parameter loss")
            self.finish()
        result=yield motor.Op(self.db.users.find({"email":email}).count)
        if result:
            self.write("邮箱已注册")
            self.finish()
            return
        num  =yield motor.Op(self.db.users.find({"urlname":name}).count)
        if num:
            urlname=name+".1"
        else:
            urlname=name
        user.update({"urlname":urlname})
        user.update({"email":email})
        user.update({"password":password})
        user.update({"name":name})
        user_id=yield motor.Op(self.db.users.insert,user)
        self.set_secure_cookie("email",email)
        self.set_secure_cookie("name",name)
        self.redirect("/")
        self.finish()
        
class  AskHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("ask.html")
    
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.engine
    def post(self):
        self.email=self.get_secure_cookie("email")
        self.title=self.get_argument("title")
        print self.title
        self.content=self.get_argument("content")
        self.tags=self.get_argument("tags")
#查找作者的信息 
        userinfo=yield motor.Op(self.db.users.find_one,{"email":self.email})
        if not userinfo:
            self.finish()
            return 
        userinfo=User(**userinfo)

        post={}
        post.update({"author":{"name":userinfo.name,"email":userinfo.email,"pic_url":userinfo.pic_url}})
        post.update({"title":self.title,"content":self.content,"tags":self.tags})
        post_id=yield motor.Op(self.db.posts.insert,post)
        self.finish()
        return
 

class TagsHandler(BaseHandler):
 
    def get(self):
        pass


    def post(self):
        pass


class SearchHandler(BaseHandler):
    def get(self):
        pass


class PersonalPageHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self,name):
        userinfo=yield motor.Op(self.db.users.find_one,{"urlname":name})
        userinfo=User(**userinfo)
        self.render("personalpage.html",userinfo=userinfo)


     
            
