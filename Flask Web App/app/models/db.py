from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin

import datetime
db = SQLAlchemy()

class BaseModel(db.Model, SerializerMixin):
    """Base data model for all objects"""
    __abstract__ = True
    # def __init__(self, *args):
    # #     super().__init__(*args)
    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        """Define a base way to print models"""
        return '%s(%s)' % (self.__class__.__name__, {
            column: value
            for column, value in self.to_dict().items()
        })
    # def json(self):
    #     """
    #     Define a base way to jsonify models, dealing with datetime objects
    #     """
    #     return {
    #         column: value if not isinstance(value, datetime.date) else value.strftime('%Y-%m-%d')
    #         for column, value in self.to_dict().items()
    #     }