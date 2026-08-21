import os
import mysql.connector
import google.generativeai as genai
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="AI_Study_Planner"
)

print("Database Connected Successfully!")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")