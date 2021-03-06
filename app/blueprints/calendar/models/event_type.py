from sqlalchemy import or_, exists
import string
import random

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db


class EventType(ResourceMixin, db.Model):
    __tablename__ = 'event_types'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    event_type_id = db.Column(db.BigInteger, unique=True, index=True, nullable=False)
    title = db.Column(db.String(255), unique=False, index=True)
    description = db.Column(db.String, unique=False, index=True)
    duration_minutes = db.Column(db.Integer)
    tag = db.Column(db.String, unique=False, index=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, user_id, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(EventType, self).__init__(**kwargs)
        self.event_type_id = EventType.generate_id()
        self.user_id = user_id
        self.active = True

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def generate_id(cls, size=8):
        # Generate a random 8-character id
        chars = string.digits
        result = int(''.join(random.choice(chars) for _ in range(size)))

        # Check to make sure there isn't already that id in the database
        if not db.session.query(exists().where(cls.event_type_id == result)).scalar():
            return result
        else:
            EventType.generate_id()

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return EventType.query.filter(
            (EventType.id == identity).first())

    @classmethod
    def search(cls, query):
        """
        Search a resource by 1 or more fields.

        :param query: Search query
        :type query: str
        :return: SQLAlchemy filter
        """
        if not query:
            return ''

        search_query = '%{0}%'.format(query)
        search_chain = (EventType.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: EventType of ids to be deleted
        :type ids: event_type
        :return: int
        """
        delete_count = 0

        for id in ids:
            event_type = EventType.query.get(id)

            if event_type is None:
                continue

            event_type.delete()

            delete_count += 1

        return delete_count