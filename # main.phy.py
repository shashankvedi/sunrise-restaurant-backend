# main.py

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
from pydantic import BaseModel, Field
from typing import List

# --- Configuration ---
# These values are loaded from the "Environment" tab in your Render dashboard.
# This is a secure way to handle secret keys.
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER") # e.g., +917007200604

# --- Initialize FastAPI App ---
app = FastAPI(title="Sunrise Restaurant API")

# --- Initialize Twilio Client ---
# This will only work if the environment variables are set.
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    client = None
    print("WARNING: Twilio credentials not found. SMS sending will be disabled.")


# --- CORS (Cross-Origin Resource Sharing) Configuration ---
# This allows your frontend webpage to communicate with this backend.
# IMPORTANT: Replace "https://your-frontend-app.netlify.app" with your actual live frontend URL.
origins = [
    "https://your-frontend-app.netlify.app", # Your deployed frontend URL
    # For local testing:
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (POST, GET, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- Pydantic Data Models ---
# These models define the exact structure of the data your API expects to receive.
# If the incoming data doesn't match this structure, FastAPI automatically sends an error.

class OrderItem(BaseModel):
    name: str
    quantity: int

class Order(BaseModel):
    # The alias allows the frontend to send "tableNumber" and FastAPI to use "table_number"
    table_number: str = Field(..., alias="tableNumber")
    customer_name: str = Field(..., alias="customerName")
    items: List[OrderItem]
    total_price: float = Field(..., alias="totalPrice")

# --- API Endpoints ---

@app.get("/")
def read_root():
    """A simple endpoint to check if the API is running."""
    return {"status": "Sunrise Restaurant API is running!"}


@app.post("/api/send-order")
def send_order(order: Order):
    """
    Receives an order from the frontend, formats it,
    and sends it as an SMS via Twilio.
    """
    if not client:
        raise HTTPException(
            status_code=500, 
            detail="Twilio client is not configured on the server. Cannot send SMS."
        )

    try:
        # 1. Format the SMS message for clarity
        message_body = (
            f"New Order: Sunrise Restaurant\n\n"
            f"Table: {order.table_number}\n"
            f"Name: {order.customer_name}\n\n"
            f"--- Items ---\n"
        )
        for item in order.items:
            message_body += f"- {item.quantity} x {item.name}\n"
        
        message_body += f"\nTotal: ₹{order.total_price:.2f}"

        # 2. Send the message using the Twilio client
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=YOUR_PHONE_NUMBER
        )

        # 3. Return a success response to the frontend
        print(f"Successfully sent SMS with SID: {message.sid}")
        return {"status": "success", "message_sid": message.sid}

    except Exception as e:
        # 4. If anything goes wrong, print the error and return an error response
        print(f"Error sending SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

