import json
from flask import Flask, redirect, request, jsonify
from sqlalchemy import create_engine, Column, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import stripe

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/stripe"

stripe.api_key = 'sk_test_51NYDnjK24O07gDqUgeLekHazMKJm3hXggZea4zV8YyySQXnqBJ9XnI8zD84vTGAkOhAyHzok7Krbs6iqikOhM2rF00tGaGOhVZ'

app = Flask(__name__, static_url_path='', static_folder='public')

DOMAIN = 'http://localhost:4242'

# Database setup
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class Payment(Base):
    __tablename__ = 'payments'
    payment_id = Column(Integer, primary_key=True)
    amount = Column(Integer)
    payment_status = Column(Boolean)

Base.metadata.create_all(engine)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': 'price_1NYDvyK24O07gDqUIv1Rm9kl',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url= DOMAIN + '/success.html',
            cancel_url=DOMAIN + '/cancel.html',
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    event = None
    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key, stripe.api_version
        )
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400

    if event.type == 'checkout.session.completed':
        session_id = event.data.object.id
        session = stripe.checkout.Session.retrieve(session_id)

        amount = session.amount_total
        payment_status = session.payment_status == 'paid'

        # Save the payment information in the database
        payment = Payment(amount=amount, payment_status=payment_status)
        session.add(payment)
        session.commit()

    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(port=4242)
