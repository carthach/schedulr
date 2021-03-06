__author__ = 'Ricky'

from flask import Flask, render_template
from flask_mail import Mail, Message
from app.app import create_celery_app

celery = create_celery_app()


def send_creator_welcome_email(email):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("You've successfully signed up for Schedulr!",
                  sender="ricky@getschedulr.com",
                  recipients=[email])

    msg.html = render_template('user/mail/creator_welcome_email.html')

    mail.send(msg)


def send_member_welcome_email(email, domain):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("You've successfully signed up for Schedulr!",
                  sender="ricky@getschedulr.com",
                  recipients=[email])

    msg.html = render_template('user/mail/member_welcome_email.html', domain=domain)

    mail.send(msg)


def send_temp_password_email(email, password, domain):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("Thanks for leaving feedback for " + domain.title() + "!",
                  sender="ricky@getschedulr.com",
                  recipients=[email])
    msg.html = render_template('user/mail/temp_password_email.html', password=password, domain=domain)

    mail.send(msg)

    print("Sent email")


def contact_us_email(email, message):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("[Schedulr Contact] Support request from " + email,
                  recipients=["ricky@getschedulr.com"],
                  sender="ricky@getschedulr.com",
                  reply_to=email)
    msg.body = email + " sent you a message:\n\n" + message

    response = Message("Your email to Schedulr has been received.",
                       recipients=[email],
                       sender="ricky@getschedulr.com")

    response.html = render_template('user/mail/contact_email.html', email=email, message=message)

    mail.send(msg)
    mail.send(response)


def send_cancel_email(email):
    app = Flask(__name__)
    mail = Mail()
    mail.init_app(app)
    msg = Message("Goodbye from Schedulr",
                  sender="ricky@getschedulr.com",
                  recipients=[email])

    msg.html = render_template('user/mail/cancel_email.html')

    mail.send(msg)
