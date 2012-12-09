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

class Comment(MotorDocument):
    name=StringField()
    content=StringField()
    pic_url=StringField()
    email=StringField()
    author_url=StringField()
   


class EmbeddedComment(Comment,EmbeddedDocument):
    pass

class Author(MotorDocument):
    urlname=StringField()
    name=StringField()
    email=StringField()
    pic_url=StringField()

class EmbeddedAuthor(Author,EmbeddedDocument):
    pass


class Post(MotorDocument):
    'a page '

    _id=ObjectIdField()
    id=_id
    title = StringField(default='')
    content = StringField(default='')
    author=EmbeddedDocumentField(EmbeddedAuthor)
    pub_date=DateTimeField()
    tags= SortedListField(StringField())
    vote=IntField()
    comments=SortedListField(EmbeddedDocumentField(EmbeddedComment))
    viewnum=IntField()
    formattime=StringField()

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
    tags=SortedListField(EmbeddedDocumentField(EmbeddedTag))
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

class Tag(MotorDocument):
    _id=ObjectId
    id=_id
    name=StringField()
    introduce=StringField()

