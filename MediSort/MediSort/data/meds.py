import os
import sqlite3
from datetime import datetime, timedelta

def create_database():
    """Create the meds.db database with initial structure and sample data"""

    # Create data directory if it doesn't exist
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    db_path = os.path.join(data_dir, "meds.db")

    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create medicines table
    cursor.execute('''
        CREATE TABLE medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            expiry_date DATE NOT NULL,
            batch_number TEXT,
            quantity INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Create medicine_scans table
    cursor.execute('''
        CREATE TABLE medicine_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            scan_image_path TEXT,
            ocr_text TEXT,
            confidence_score REAL,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (medicine_id) REFERENCES medicines (id)
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX idx_medicines_user_id ON medicines(user_id)')
    cursor.execute('CREATE INDEX idx_medicines_expiry ON medicines(expiry_date)')
    cursor.execute('CREATE INDEX idx_medicines_name ON medicines(name)')

    # Insert sample user (password: "admin123" -> hashed)
    import hashlib
    admin_password = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute('''
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
    ''', ("admin", "admin@medisort.com", admin_password))

    # Insert sample medicines with various expiry dates
    sample_medicines = [
        ("Paracetamol 500mg", 1, (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'), "BATCH001", 25),
        ("Ibuprofen 400mg", 1, (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'), "BATCH002", 3),
        ("Aspirin 75mg", 1, (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d'), "BATCH003", 50),
        ("Amoxicillin 250mg", 1, (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'), "BATCH004", 8),
        ("Vitamin D3", 1, (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'), "BATCH005", 100),
        ("Cough Syrup", 1, (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'), "BATCH006", 2),
        ("Antacid Tablets", 1, (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'), "BATCH007", 15),
        ("Bandages", 1, (datetime.now() + timedelta(days=720)).strftime('%Y-%m-%d'), "BATCH008", 4),
    ]

    for medicine in sample_medicines:
        cursor.execute('''
            INSERT INTO medicines (name, user_id, expiry_date, batch_number, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', medicine)

    conn.commit()
    conn.close()

    print(f"Database created successfully at: {db_path}")
    print("Sample user created:")
    print("  Username: admin")
    print("  Password: admin123")
    print(f"Sample medicines added: {len(sample_medicines)}")

if __name__ == "__main__":
    create_database()