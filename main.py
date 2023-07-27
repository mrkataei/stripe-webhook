import json, os, stripe
from flask import Flask, redirect, request, jsonify
from sqlalchemy import create_engine, Column, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='public')

DOMAIN = 'http://localhost:4242'
stripe.api_key = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

print(DATABASE_URL)
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

    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object # contains a stripe.PaymentIntent
        print(payment_intent)
        amount = payment_intent.amount
        status = payment_intent.status == 'succeeded'
        # Save the payment information in the database
        try:
            payment = Payment(amount=amount, payment_status=status)
            session.add(payment)
            session.commit()
        except Exception as e:
            print(e)
        print('PaymentIntent was successful!')
        
    elif event.type == 'payment_method.attached':
        payment_method = event.data.object # contains a stripe.PaymentMethod
        print('PaymentMethod was attached to a Customer!')
    # ... handle other event types
    else:
        print('Unhandled event type {}'.format(event.type))
    

    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(port=4242)
