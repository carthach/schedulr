from sqlalchemy import or_, exists
import string
import random

from lib.util_sqlalchemy import ResourceMixin, AwareDateTime
from app.extensions import db
from app.blueprints.calendar.models.account import Account


class Calendar(ResourceMixin, db.Model):
    __tablename__ = 'calendars'

    # Objects.
    id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(db.BigInteger, unique=True, index=True, nullable=False)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)
    account_id = db.Column(db.Integer, db.ForeignKey(Account.account_id, onupdate='CASCADE', ondelete='CASCADE'),
                        index=True, nullable=True, primary_key=False, unique=False)

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(Calendar, self).__init__(**kwargs)
        self.calendar_id = Calendar.generate_id()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def generate_id(cls, size=8):
        # Generate a random 8-character id
        chars = string.digits
        result = int(''.join(random.choice(chars) for _ in range(size)))

        # Check to make sure there isn't already that id in the database
        if not db.session.query(exists().where(cls.calendar_id == result)).scalar():
            return result
        else:
            Calendar.generate_id()

    @classmethod
    def find_by_id(cls, identity):
        """
        Find an email by its message id.

        :param identity: Email or username
        :type identity: str
        :return: User instance
        """
        return Calendar.query.filter(
            (Calendar.id == identity).first())

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
        search_chain = (Calendar.id.ilike(search_query))

        return or_(*search_chain)

    @classmethod
    def bulk_delete(cls, ids):
        """
        Override the general bulk_delete method because we need to delete them
        one at a time while also deleting them on Stripe.

        :param ids: Calendar of ids to be deleted
        :type ids: calendar
        :return: int
        """
        delete_count = 0

        for id in ids:
            calendar = Calendar.query.get(id)

            if calendar is None:
                continue

            calendar.delete()

            delete_count += 1

        return delete_count
