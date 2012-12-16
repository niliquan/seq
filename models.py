import datetime
from bson.objectid import ObjectId
from dictshield.fields import StringField, IntField, DateTimeField
from dictshield.document  import Document, EmbeddedDocument
from dictshield.fields.compound  import SortedListField, EmbeddedDocumentField

from dictshield.fields.mongo import ObjectIdField
class MotorDocument(Document):
    @property
    def date_created(self):
        return self.id.generation_time

    class Meta:
        id_field=ObjectIdField

class Author(MotorDocument):
    urlname=StringField()
    name=StringField()
    email=StringField()
    pic_url=StringField()

class EmbeddedAuthor(Author,EmbeddedDocument):
    pass

class Comment(MotorDocument):
    content=StringField()
    email=StringField()
    author=EmbeddedDocumentField(EmbeddedAuthor)
    
   


class EmbeddedComment(Comment,EmbeddedDocument):
    pass




class Post(MotorDocument):
    'a page '
    _id=ObjectIdField()
    id=_id
    title = StringField(default='')
    content = StringField(default='')
    author=EmbeddedDocumentField(EmbeddedAuthor)
    pub_date=DateTimeField()
    tags=  SortedListField(StringField())
    vote=IntField()
    comments=SortedListField(EmbeddedDocumentField(EmbeddedComment))
    viewnum=IntField()
    formattime=StringField()
    authoremail=StringField()

class TagDocument(Document):
    name=StringField()
    _id=ObjectIdField()
    id=_id

class EmbeddedTag(TagDocument,EmbeddedComment):
    pass
     
class User(MotorDocument):
    _id=ObjectId
    id=_id
    name=StringField()
    email=StringField()
    tags=SortedListField(StringField())
    birthday=StringField()
    description=StringField()
    selfsite=StringField()
    pic_url=StringField()
    homepage=StringField()
    gender=StringField()
    urlname=StringField()
    address=StringField()
    follow=SortedListField(EmbeddedDocumentField(EmbeddedAuthor))
    followed=SortedListField(EmbeddedDocumentField(EmbeddedAuthor))
    followemails=SortedListField(StringField())
    followedemails=SortedListField(StringField())

class Tag(MotorDocument):
    _id=ObjectId
    id=_id
    name=StringField()
    introduce=StringField()
    followemails=SortedListField(StringField())
    pic_url=StringField()

