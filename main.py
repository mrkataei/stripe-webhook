import os
from flask import Flask, redirect, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import stripe

# Replace with your actual PostgreSQL database connection string
DATABASE_URL = "postgresql://your_username:your_password@localhost:5432/your_database"

stripe.api_key = 'sk_test_51NYDnjK24O07gDqUgeLekHazMKJm3hXggZea4zV8YyySQXnqBJ9XnI8zD84vTGAkOhAyHzok7Krbs6iqikOhM2rF00tGaGOhVZ'

app = Flask(__name__, static_url_path='', static_folder='public')

YOUR_DOMAIN = 'http://localhost:4242'

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

# Create the table if it doesn't exist
Base.metadata.create_all(engine)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': '{{PRICE_ID}}',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
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
            payload, stripe.api_key, stripe.api_version
        )
    except ValueError as e:
        return jsonify(success=False, error=str(e)), 400

    # Handle the event based on its type
    if event.type == 'checkout.session.completed':
        session_id = event.data.object.id
        session = stripe.checkout.Session.retrieve(session_id)

        # Get payment details from the session
        amount = session.amount_total
        payment_status = session.payment_status == 'paid'

        # Save the payment information in the database
        payment = Payment(amount=amount, payment_status=payment_status)
        session.add(payment)
        session.commit()

    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(port=4242)
