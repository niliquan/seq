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

def checkinfo(result,error):
    if error:
        print "no info"
    else:
        print"OK"

def check_last_modified(get):
    @functools.wraps(get)
    @tornado.web.asynchronous
    @gen.engine
    def _get(self,*args,**kwargs):
        page_num=kwargs.get("page_num")
        if page_num!=0 and page_num:
            page_num=page_num.rstrip("/")
        if not page_num:
            page_num=0
        kwargs.update({"page_num":page_num})
        postdocs =yield motor.Op(self.get_posts,*args,**kwargs)
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
        self.render("detail.html",post=postdoc)


class HomeHandler(BaseHandler):

    def get_posts(self,callback=checkinfo,page_num=0):
        (self.db.posts.find()
                .sort([('pub_date',-1)]).skip(int(page_num)*10)
            .limit(10).to_list(callback=callback))
    
    @tornado.web.addslash
    @check_last_modified
    def get(self,page_num=0):
        email=self.get_secure_cookie("email")
        self.page_num=page_num
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if userinfo:
            userinfo=User(**userinfo)
        self.render('home.html',
                posts=self.posts,
                userinfo=userinfo,
                page_num=int(self.page_num))
  

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
       
        email=self.get_secure_cookie("email")
 
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if not email and not  userinfo:
            self.redirect("/")
            return

        id=userinfo["_id"]
        userinfo.update({
            "name":self.get_argument("name"),
            "address":self.get_argument("address"),
            "homepage":self.get_argument("homepage"),
            "birthday":self.get_argument("birthday"),
            "description":self.get_argument("description")})

#上传图片
        storename=None
        if  self.request.files and self.request.files["avatar"][0]:
            send_file=self.request.files["avatar"][0]
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
            image_one.save(tmp_name)
            tmp_file.close()

        if storename:
            userinfo.update({"pic_url":storename})

#修改用户数据
        user_id=yield motor.Op(self.db.users.update,{"_id":id},userinfo)
        self.set_secure_cookie("name",self.get_argument("name"))
        self.redirect("/")
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
        self.content=self.get_argument("content")
        self.tags=self.get_argument("tags")
#查找作者的信息 
        userinfo=yield motor.Op(self.db.users.find_one,{"email":self.email})
        if not userinfo:
            self.finish()
            return 
        userinfo=User(**userinfo)
        posttime=time.time()
        formattime=time.strftime("%Y-%m-%d",time.localtime(posttime))
        post={}
        post.update({"author":{"name":userinfo.name,
            "urlname":userinfo.urlname,
            "email":userinfo.email,
            "pic_url":userinfo.pic_url}})
        post.update({"title":self.title,
            "content":self.content,
            "tags":self.tags,
            "pub_date":posttime,
            "formattime":formattime,
            })
        post_id=yield motor.Op(self.db.posts.insert,post)
        self.redirect("/")
        self.finish()
        return
 
class AnswerHandler(BaseHandler):

    def get(self):
        pass

    @tornado.web.asynchronous
    @gen.engine
    def post(self):

        self.email=self.get_secure_cookie("email")
        userinfo=yield motor.Op(self.db.users.find_one,{"email":self.email})
        userinfo=User(**userinfo)
        content=self.get_argument("content")
        id=self.get_argument("id")
        if not content and not userinfo and not id:
            self.write("missing ")
            self.finish()
            return
               
        comment={"author_url":userinfo.urlname,
                "name":userinfo.name,
                "pic_url":userinfo.pic_url,
                "content":content,
                "email":userinfo.email}

        id=self.get_argument("id")
        id=ObjectId(id)
        result=yield motor.Op(self.db.posts.update,{"_id":id},{"$addToSet":{"comments":comment}})
        self.redirect("/")

class TagsHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        email=self.get_secure_cookie("email")
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if userinfo:
            userinfo=User(**userinfo)
        self.render("tagsview.html",userinfo=userinfo)

    def post(self):
        pass

class TagDetailHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self,tagname):
        email=self.get_secure_cookie("email")
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        userinfo=User(**userinfo)
        if not tagname:
            self.write("error")
            self.finish()
            return
        taginfo=yield motor.Op(self.db.tags.find,{"name":tagname})
        if not taginfo:
            self
        self.render("tag.html")
    
    def post(self):
        pass

class SearchHandler(BaseHandler):
    def get(self):
        q=self.get_argument("q")
        limit=self.get_argument("limit")

        posts=yield motor.Op(self.db.posts.find,{})

class PersonalPageHandler(BaseHandler):

    def get_questions(self,callback=checkinfo,page_num=0,condition={}):
        (self.db.posts.find(condition).skip(int(page_num)*14).sort([('pub_date',-1)]).limit(10).to_list(callback=callback))  
  
    @tornado.web.asynchronous
    @gen.engine
    def get(self,name):
        userinfo=yield motor.Op(self.db.users.find_one,{"urlname":name})
        userinfo=User(**userinfo)
        condition={"author.email":userinfo.email}
        questions = yield motor.Op(self.get_questions,condition=condition)
        self.questions=[Post(**question) for question in questions]
        if userinfo.urlname==name:
            show= False
        self.render("personalpage.html", userinfo=userinfo , questions=self.questions,show=show)

class AttentionHandler(BaseHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        tagname=self.get_argument("tagname")
        email=self.get_secure_cookie("email")
        if not email:
            self.redirect("/user/login")
            self.finish()
            return
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if not userinfo:
            self.write("no that user")
        id=userinfo[_id]
        result=yield motor.Op(self.db.users.update,{"_id":id},{"$addToSet":{"tags":{"name":tagname}}})


     
            
