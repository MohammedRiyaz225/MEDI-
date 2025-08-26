import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
import numpy as np

import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="meds.db"):
        self.db_path = db_path
        # ensure directory exists if path includes directories
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.init_database()

    def get_connection(self):
        # you can add check_same_thread=False if you access from threads
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Create base tables and run simple migrations for missing columns."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table (for your AuthManager)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Medicines table - contains columns your UI expects
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    quantity INTEGER DEFAULT 0,
                    expiry_date TEXT,
                    batch_number TEXT,
                    category TEXT,
                    manufacturer TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            # Table to hold raw scans / references to images (optional)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicine_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    image_path TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    result_summary TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            # ML scan results table (you already had this)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    label_region BLOB,
                    confidence REAL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_id) REFERENCES medicine_scans(id)
                )
            ''')

            conn.commit()

            # After creating base tables, ensure old DBs get missing columns added
            self._migrate_medicines_table(conn)

    def _migrate_medicines_table(self, conn):
        """
        Ensure medicines table contains expected columns. If any are missing,
        add them using ALTER TABLE ADD COLUMN (SQLite supports this).
        """
        expected_cols = {
            'user_id': 'INTEGER',
            'name': 'TEXT',
            'quantity': 'INTEGER DEFAULT 0',
            'expiry_date': 'TEXT',
            'batch_number': 'TEXT',
            'category': 'TEXT',
            'manufacturer': 'TEXT',
            'description': 'TEXT',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP'
        }

        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(medicines)")
        existing = {row[1] for row in cursor.fetchall()}  # row[1] is column name

        for col_name, col_type in expected_cols.items():
            if col_name not in existing:
                # Add the column. Keep it nullable so ALTER works on old rows.
                sql = f"ALTER TABLE medicines ADD COLUMN {col_name} {col_type}"
                try:
                    cursor.execute(sql)
                    conn.commit()
                    print(f"[DB] Added missing column medicines.{col_name}")
                except Exception as e:
                    # If ALTER fails, print but continue
                    print(f"[DB] Failed to add column {col_name}: {e}")

