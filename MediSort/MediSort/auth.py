import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import os
from datetime import datetime
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import re
from PIL import Image
import numpy as np

class AuthManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username, password):
        try:
            hashed_password = self.hash_password(password)
            with self.db_manager.get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed_password)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def login(self, username, password):
        hashed_password = self.hash_password(password)
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ? AND password = ?",
                (username, hashed_password)
            )
            row = cursor.fetchone()
            return row[0] if row else None