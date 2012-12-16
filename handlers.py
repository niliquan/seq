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
    def  get_authors(self,callback=checkinfo,condition={},condition2={}):
        (self.db.users.find(condition,condition2).to_list(callback=callback))
  


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
        author=yield motor.Op(self.db.users.find_one,{"email":postdoc.authoremail})
        postdoc.author=author
        emails=[ comment.email if comment else None for comment in postdoc.comments]
        answers=yield motor.Op(self.get_authors,
            condition={"email":{"$in":emails}},
            condition2={"name":1,"pic_url":1,"urlname":1,"email":1})
        for comment in postdoc.comments:
            for answer  in answers:
                if comment.email == answer["email"]:
                    comment.author=answer

        self.render("detail.html",post=postdoc)


class HomeHandler(BaseHandler):

    def get_posts(self,callback=checkinfo,page_num=0):
        (self.db.posts.find()
                .sort([('pub_date',-1)]).skip(int(page_num)*10)
            .limit(10).to_list(callback=callback))

    def get_tags(self,callback=checkinfo,condition={}):
        (self.db.tags.find(condition)
                .to_list(callback=callback))

    def get_authors(self,callback=checkinfo,condition={},condition2={}):
        (self.db.users.find(condition,condition2)
                .to_list(callback=callback))

    @tornado.web.asynchronous
    @gen.engine
    def get(self,page_num=0):
        email=self.get_secure_cookie("email")
        self.page_num=page_num
        if self.page_num!=0 and self.page_num:
            self.page_num.rstrip("/")
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if userinfo:
            userinfo=User(**userinfo)

        posts=yield motor.Op(self.get_posts,page_num=self.page_num)
        if posts:
            self.posts=[Post(**post) if post else None for post in posts ]
            emails= [ post.authoremail for post in self.posts]
            authors=yield motor.Op(self.get_authors,
                    condition={"email":{"$in":emails}},
                    condition2={"name":1,"urlname":1,"pic_url":1,"email":1})
           # authors=[ Author(**author) if author else None for author in authors]

        self.postdocs=[]
        if posts:
            for post in self.posts:
                for author in authors:
                    if post.authoremail==author["email"]:
                        post.author=author
                        self.postdocs.append(post)
        self.tags=[]
        if userinfo:
            self.tags=yield motor.Op(self.get_tags,condition={"name":{"$in":userinfo.tags}})
        if self.tags:
            self.tags=[ Tag(**tag) if tag else None for tag in self.tags]
        if userinfo:
            followers=yield motor.Op(self.get_authors,
                    condition={"email":{"$in":userinfo.followemails}},
                    condition2={"name":1,"urlname":1,"pic_url":1,"email":1})
            userinfo.follow=followers

        self.render('home.html',
                posts=self.postdocs,
                userinfo=userinfo,
                tags=self.tags,
                page_num=int(self.page_num))


class HomeModule(tornado.web.UIModule):

    def render(self,userinfo,tags):
        return self.render_string("module/home-side.html",userinfo=userinfo,tags=tags)



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


class AddTagHandler(BaseHandler):

    def get(self):
        self.render("addtag.html")
    
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
        
class AskHandler(BaseHandler):
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
        post.update({"title":self.title,
            "content":self.content,
            "tags":self.tags,
            "pub_date":posttime,
            "formattime":formattime,
            "authoremail":self.email,
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
               
        comment={
                "content":content,
                "email":userinfo.email}

        id=self.get_argument("id")
        id=ObjectId(id)
        result=yield motor.Op(self.db.posts.update,
                {"_id":id},
                {"$addToSet":{"comments":comment}})
        self.redirect("/")

class TagsHandler(BaseHandler):
    def get_tags(self,condition={},callback=checkinfo):
        (self.db.tags.find(condition).to_list(callback=callback))


    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        email=self.get_secure_cookie("email")
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if userinfo:
            userinfo=User(**userinfo)
        self.tags=[]
        self.tags=yield motor.Op(self.get_tags,condition={"name":{"$in":userinfo.tags}})
        if self.tags:
            self.tags=[Tag(**tag) if tag else None for tag in self.tags]
        self.render("tagsview.html",userinfo=userinfo,tags=self.tags)

    def post(self):
        pass

class TagDetailHandler(BaseHandler):

    def get_users(self,condition={},callback=checkinfo):
        (self.db.users.find(condition).limit(5).to_list(callback=callback))

    @tornado.web.asynchronous
    @gen.engine
    def get(self,tagname):
        email=self.get_secure_cookie("email")
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        if userinfo:
            userinfo=User(**userinfo)
        if not tagname:
            self.write("error")
            self.finish()
            return
        taginfo=yield motor.Op(self.db.tags.find_one,{"name":tagname})
        if not taginfo:
            self.redirect("/")
        taginfo=Tag(**taginfo)
        readyCon=False
        users=yield motor.Op(self.get_users,condition={"email":{"$in":taginfo.followemails}})
        followcount=len(taginfo.followemails)
        self.users=[]
        if users:
            self.users=[ User(**user) if user else None for user in users]
        if userinfo:
            readyCon=checkTagCon(userinfo,tagname)
        self.render("tag.html",
                taginfo=taginfo,
                al=readyCon,
                users=self.users,
                count=followcount)
    
    def post(self):
        pass

class SearchHandler(BaseHandler):
    def get(self):
        q=self.get_argument("q")
        limit=self.get_argument("limit")

        posts=yield motor.Op(self.db.posts.find,{})

class PersonalPageHandler(BaseHandler):

    def get_posts(self,callback=checkinfo,page_num=0,condition={}):
        (self.db.posts.find(condition).
                skip(int(page_num)*14).
                sort([('pub_date',-1)]).
                limit(10).to_list(callback=callback))  
  
    @tornado.web.asynchronous
    @gen.engine
    def get(self,name):
        userinfo=yield motor.Op(self.db.users.find_one,{"urlname":name})
        userinfo=User(**userinfo)
        condition={"author.email":userinfo.email}
        questions = yield motor.Op(self.get_posts,condition=condition)
        self.questions=[Post(**question) for question in questions]
        show=True
        readlycontain=True
        email=self.get_secure_cookie("email")
        admin=yield motor.Op(self.db.users.find_one,{"email":email})
        if admin:
            admin=User(**admin)
            if admin.urlname==name or not admin:
                show= False
            readlycontain=check_contain(userinfo.email,admin.follow)

        condition1={"comments.email":userinfo.email}
        answers = yield motor.Op(self.get_posts,condition=condition1)
        answers =[Post(**answer) for answer in answers]
        self.render("personalpage.html",
                userinfo=userinfo,
                questions=self.questions,
                show=show,answers=answers,al=readlycontain)

def check_contain(email,follow):
    for f in follow:
        print f.email
        if email==f.email:
            return True
    return False


class TagAttentionHandler(BaseHandler):

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
        id=userinfo["_id"]
        result=yield motor.Op(self.db.users.update,
                {"_id":id},
                {"$addToSet":{"tags":tagname}})
        taginfo=yield motor.Op(self.db.tags.find_one,{"name":tagname})
        result1=yield motor.Op(self.db.tags.update,
                {"_id":taginfo["_id"]},
                {"$addToSet":{"followemails":userinfo["email"]}})
        self.finish()

def checkTagCon(userinfo,tagname):
    for tag in userinfo.tags:
        if tagname==tag:
            return True
    return False


class UnfollowTagHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        tagname=self.get_argument("tagname")
        email=self.get_secure_cookie("email")
        if not email:
            self.redirect("/")
            self.finish()
            return
        userinfo=yield motor.Op(self.db.users.find_one,{"email":email})
        taginfo=yield motor.Op(self.db.tags.find_one,{"name":tagname})
        if not taginfo:
            self.redirct("/")
            return
        id=userinfo["_id"]
        result=yield motor.Op(self.db.users.update,
                {"_id":id},
                {"$pull":{"tags":tagname}})
        result1=yield motor.Op(self.db.tags.update,
                {"_id":taginfo["_id"]},
                {"$pull":{"followemails":email}})
        self.finish()




class UserInfoModule(tornado.web.UIModule):
    def render(self,userinfo,show,al):
        return self.render_string("module/userinfo.html",
                userinfo=userinfo,
                show=show,
                al=al)
    
    def javascript_files(self):
        return "js/attention.js"



class TagModule(tornado.web.UIModule):
    def render(self,taginfo,al,users,count):
        return self.render_string("module/tag-side.html",
                taginfo=taginfo,
                al=al,
                users=users,
                count=count)

    def javascript_files(self):
        return "js/attention.js"


class PersonFollowHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):

        #关注者的信息
        self.email=self.get_secure_cookie("email");
        if not self.email:
            self.redirct("/")
        userinfo=yield motor.Op(self.db.users.find_one,
                {"email":self.email})
        if not userinfo:
            self.redirect("/")
        userinfo=User(**userinfo)


        #被关注者的信息
        followerEmail=self.get_argument("followemail")
        followinfo=yield motor.Op(self.db.users.find_one,{"email":followerEmail})
        if not followinfo:
            self.redirect("/")
        followinfo=User(**followinfo)

#关注者插入一条关注他人的信息
        result=yield motor.Op(self.db.users.update,
                {"_id":userinfo.id},
                {"$addToSet":{"followemails":followerEmail}})

#被关注者插入一条被观者的信息
        result1=yield motor.Op(self.db.users.update,
                {"_id":followinfo.id},
                {"$addToSet":{"followedemails":userinfo.email}})

        self.finish()
       
 
class PersonUnfollowHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        adminEmail=self.get_secure_cookie("email")
        if not adminEmail:
            self.redirect("/login")
        admin=yield motor.Op(self.db.users.find_one,{"email":adminEmail})
        admin=User(**admin)


        unfollowemail=self.get_argument("followemail")
        followedinfo=yield motor.Op(self.db.users.find_one,{"email":unfollowemail})
        followedinfo=User(**followedinfo)

        result1=yield motor.Op(self.db.users.update,
                {"_id":admin.id},
                {"$pull":{"follow":{"urlname":followedinfo.urlname}}})

        result2=yield motor.Op(self.db.users.update,
                {"_id":followedinfo.id},
                {"$pull":{"followed":{"urlname":admin.urlname}}})
        self.finish()

