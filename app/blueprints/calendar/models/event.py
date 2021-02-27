from sqlalchemy import or_, exists
import string
import random
from app.blueprints.calendar.models.calendar import Calendar
from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db


class Event(ResourceMixin, db.Model):
    __tablename__ = 'events'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.BigInteger, unique=True, index=True, nullable=False)
    requester_name = db.Column(db.String(255), unique=False, index=True)
    requester_email = db.Column(db.String(255), unique=False, index=True)
    notes = db.Column(db.String, unique=False, index=True)
    zoom = db.Column(db.String, unique=False, index=True)
    event_datetime = db.Column(AwareDateTime())
    date = db.Column(db.String(255))
    start_time = db.Column(db.Time)
    tz_offset = db.Column(db.String(255))
    duration_minutes = db.Column(db.Integer)

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)
    calendar_id = db.Column(db.BigInteger, db.ForeignKey(Calendar.calendar_id, onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)
    event_type_id = db.Column(db.BigInteger, db.ForeignKey('event_types.event_type_id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, user_id, calendar_id=None, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Event, self).__init__(**kwargs)
        self.event_id = Event.generate_id()
        self.user_id = user_id

        if calendar_id is not None:
            self.calendar_id = calendar_id

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def generate_id(cls, size=8):
        # Generate a random 8-character id
        chars = string.digits
        result = int(''.join(random.choice(chars) for _ in range(size)))

        # Check to make sure there isn't already that id in the database
        if not db.session.query(exists().where(cls.event_id == result)).scalar():
            return result
        else:
            Event.generate_id()

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return Event.query.filter(
            (Event.id == identity).first())

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
        search_chain = (Event.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Event of ids to be deleted
        :type ids: event
        :return: int
        """
        delete_count = 0

        for id in ids:
            event = Event.query.get(id)

            if event is None:
                continue

            event.delete()

            delete_count += 1

        return delete_count


# class Event:
#
#     tags = ''
#
#     def __init__(self, event):
#         self.description = event['body_html']
#         self.title = event['title']
#         self.created = event['created_at']
#         self.event_id = event['id']
#         self.images = event['images']
#         self.options = event['options']
#         self.variants = event['variants']