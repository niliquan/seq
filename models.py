import datetime
from bson.objectid import ObjectId
from dictshield.fields import StringField, IntField, DateTimeField
from dictshield.document  import Document, EmbeddedDocument
from dictshield.fields.compound  import SortedListField, EmbeddedDocumentField

from dictshield.fields.mongo import ObjectIdField
class PostDocument(Document):
    @property
    def date_created(self):
        return self.id.generation_time

    class Meta:
        id_field=ObjectIdField

class Post(PostDocument):
    'a page '
    title = StringField(default='')
    body = StringField(default='')
    author= StringField(default='niliquan')
