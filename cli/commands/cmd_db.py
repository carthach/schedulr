import click
from sqlalchemy_utils import database_exists, create_database
from app.app import create_app
from app.extensions import db
from app.blueprints.base.functions import generate_id
from app.blueprints.user.models.user import User
from app.blueprints.shopify.models.plan import Plan
from app.blueprints.calendar.models.calendar import Calendar
from app.blueprints.calendar.models.event_type import EventType
from app.blueprints.calendar.models.event import Event

# Create an app context for the database connection.
app = create_app()
db.app = app


@click.group()
def cli():
    """ Run PostgreSQL related tasks. """
    pass


@click.command()
@click.option('--with-testdb/--no-with-testdb', default=False,
              help='Create a test db too?')
def init(with_testdb):
    """
    Initialize the database.

    :param with_testdb: Create a test database
    :return: None
    """
    db.drop_all()

    db.create_all()

    if with_testdb:
        db_uri = '{0}_test'.format(app.config['SQLALCHEMY_DATABASE_URI'])

        if not database_exists(db_uri):
            create_database(db_uri)


@click.command()
def seed_users():
    """
    Seed the database with an initial user.

    :return: User instance
    """
    if User.find_by_identity(app.config['SEED_ADMIN_EMAIL']) is not None:
        return None

    admin = {
        'role': 'admin',
        'email': app.config['SEED_ADMIN_EMAIL'],
        'username': app.config['SEED_ADMIN_USERNAME'],
        'password': app.config['SEED_ADMIN_PASSWORD'],
        'name': 'Admin'
    }

    owner = {
        'role': 'owner',
        'email': app.config['SEED_OWNER_EMAIL'],
        'username': app.config['SEED_OWNER_USERNAME'],
        'password': app.config['SEED_ADMIN_PASSWORD'],
        'name': 'Ricky Charpentier'
    }

    User(**owner).save()

    return User(**admin).save()


@click.command()
def seed_events():
    """
    Seed the database with an initial user.

    :return: User instance
    """

    u = User.query.filter(User.email == app.config['SEED_OWNER_EMAIL']).scalar()

    calendar = {
        'user_id': u.id
    }

    c = Calendar(**calendar)
    c.save()

    event_type_30 = {
        'user_id': u.id,
        'title': 'Standard 30 minute meeting',
        'description': 'This is the standard length, 30-minute meeting. Not too long, not too short.',
        'duration_minutes': 30
    }

    event_type_60 = {
        'user_id': u.id,
        'title': '60 minute meeting',
        'description': 'A meeting that\'s a bit longer. You\'re starting to get bored. When will it end?',
        'duration_minutes': 60,
        'active': False
    }

    event_type_15 = {
        'user_id': u.id,
        'title': 'A short meeting (15 minutes)',
        'description': 'This is a short, quick chat that is only supposed to take 15 minutes. Will it?',
        'duration_minutes': 60,
        'active': False
    }

    e_30 = EventType(**event_type_30)
    e_60 = EventType(**event_type_60)

    e_30.save()
    e_60.save()

    return EventType(**event_type_15).save()


@click.command()
def seed_plans():
    """
    Seed the database with plans.

    :return: Plan instance
    """

    hobby = {
        'title': 'Hobby',
        'tag': 'hobby',
        'limit': 100,
        'price': 19
    }

    startup = {
        'title': 'Startup',
        'tag': 'startup',
        'limit': 500,
        'price': 39
    }

    business = {
        'title': 'Business',
        'tag': 'business',
        'limit': 1000,
        'price': 69
    }

    enterprise = {
        'title': 'Enterprise',
        'tag': 'enterprise',
        'limit': 5000,
        'price': 129
    }

    unlimited = {
        'title': 'Unlimited',
        'tag': 'unlimited',
        'limit': 999999,
        'price': 199
    }

    Plan(**hobby).save()
    Plan(**startup).save()
    Plan(**business).save()
    Plan(**enterprise).save()

    return Plan(**unlimited).save()


@click.command()
@click.option('--with-testdb/--no-with-testdb', default=False,
              help='Create a test db too?')
@click.pass_context
def reset(ctx, with_testdb):
    """
    Init and seed_users automatically.

    :param with_testdb: Create a test database
    :return: None
    """
    ctx.invoke(init, with_testdb=with_testdb)
    ctx.invoke(seed_users)
    ctx.invoke(seed_plans)
    ctx.invoke(seed_events)

    return None


@click.command()
def backup():
    """
    Backup the db.
    :return: None
    """
    # from flask.alchemydumps import AlchemyDumps
    #
    # alchemydumps = AlchemyDumps(app, db)
    #
    # return alchemydumps.create()
    return None


cli.add_command(init)
cli.add_command(seed_users)
cli.add_command(seed_plans)
cli.add_command(seed_events)
cli.add_command(reset)
