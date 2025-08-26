import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import cv2
import pytesseract
import re
import os
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import numpy as np
import threading
import json

# Set Tesseract path (adjust as needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Try to import ML components
try:
    import easyocr
    import tensorflow as tf
    from tensorflow import keras
    ML_AVAILABLE = True
    print("✓ ML components loaded successfully")
except ImportError as e:
    ML_AVAILABLE = False
    print(f"⚠ ML components not available: {e}")

class EnhancedMediSortMainApp:
    """
    Main MediSort application with enhanced manual/auto scan integration
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MediSort Pro - Smart Medicine Inventory")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')

        # Initialize database (simplified for demo)
        self.db_path = "medisort.db"
        self.init_database()

        # Current user (simplified - in real app would have proper auth)
        self.current_user_id = 1

        self.create_main_interface()

    def init_database(self):
        """Initialize database with medicines table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    name TEXT NOT NULL,
                    quantity INTEGER DEFAULT 0,
                    expiry_date TEXT,
                    batch_number TEXT,
                    manufacturer TEXT,
                    category TEXT DEFAULT 'Other',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
            print("✓ Database initialized")

        except Exception as e:
            print(f"Database initialization error: {e}")

    def create_main_interface(self):
        """Create the main application interface"""
        # Header
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="🏥 MediSort Pro",
                              font=('Arial', 24, 'bold'),
                              bg='#34495e', fg='#ecf0f1')
        title_label.pack(side=tk.LEFT, padx=20, pady=20)

        # Enhanced scan button (prominent)
        scan_btn = tk.Button(header_frame, text="🔬 Smart Scanner",
                            command=self.open_enhanced_scanner,
                            font=('Arial', 16, 'bold'),
                            bg='#e74c3c', fg='white',
                            width=15, height=2,
                            relief=tk.FLAT, cursor='hand2')
        scan_btn.pack(side=tk.RIGHT, padx=20, pady=15)

        # Main content area
        content_frame = tk.Frame(self.root, bg='#ecf0f1')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Manual entry form
        form_frame = tk.LabelFrame(content_frame, text="📝 Manual Entry",
                                  font=('Arial', 14, 'bold'),
                                  bg='#ffffff', fg='#2c3e50')
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)

        self.create_medicine_form(form_frame)

        # Right panel - Medicine list
        list_frame = tk.LabelFrame(content_frame, text="📋 Medicine Inventory",
                                  font=('Arial', 14, 'bold'),
                                  bg='#ffffff', fg='#2c3e50')
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=5)

        self.create_medicine_list(list_frame)

        # Load existing medicines
        self.load_medicines()

    def create_medicine_form(self, parent):
        """Create medicine entry form"""
        form_container = tk.Frame(parent, bg='#ffffff')
        form_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Form fields
        fields = [
            ("Medicine Name*:", 'name'),
            ("Quantity*:", 'quantity'),
            ("Expiry Date (YYYY-MM-DD):", 'expiry'),
            ("Batch Number:", 'batch'),
            ("Manufacturer:", 'manufacturer')
        ]

        self.form_entries = {}

        for i, (label_text, field_name) in enumerate(fields):
            tk.Label(form_container, text=label_text, font=('Arial', 11, 'bold'),
                    bg='#ffffff', fg='#2c3e50').grid(row=i, column=0, sticky='w', pady=8)

            entry = tk.Entry(form_container, font=('Arial', 11), width=30)
            entry.grid(row=i, column=1, padx=(10, 0), pady=8, sticky='ew')
            self.form_entries[field_name] = entry

        # Category dropdown
        tk.Label(form_container, text="Category:", font=('Arial', 11, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=len(fields), column=0, sticky='w', pady=8)

        self.category_var = tk.StringVar(value='Tablet')
        category_combo = ttk.Combobox(form_container, textvariable=self.category_var,
                                     values=['Tablet', 'Capsule', 'Syrup', 'Injection',
                                            'Cream', 'Drops', 'Inhaler', 'Other'],
                                     font=('Arial', 11), width=27)
        category_combo.grid(row=len(fields), column=1, padx=(10, 0), pady=8, sticky='ew')

        # Notes/Description
        tk.Label(form_container, text="Notes:", font=('Arial', 11, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=len(fields)+1, column=0, sticky='nw', pady=8)

        self.notes_text = tk.Text(form_container, font=('Arial', 10), width=30, height=4)
        self.notes_text.grid(row=len(fields)+1, column=1, padx=(10, 0), pady=8, sticky='ew')

        # Configure grid weights
        form_container.columnconfigure(1, weight=1)

        # Buttons
        button_frame = tk.Frame(form_container, bg='#ffffff')
        button_frame.grid(row=len(fields)+2, column=0, columnspan=2, pady=20, sticky='ew')

        # Add medicine button
        add_btn = tk.Button(button_frame, text="➕ Add Medicine",
                           command=self.add_medicine_manual,
                           font=('Arial', 12, 'bold'),
                           bg='#27ae60', fg='white',
                           width=20, height=2,
                           relief=tk.FLAT, cursor='hand2')
        add_btn.pack(pady=5, fill=tk.X)

        # Clear form button
        clear_btn = tk.Button(button_frame, text="🧹 Clear Form",
                             command=self.clear_form,
                             font=('Arial', 11, 'bold'),
                             bg='#95a5a6', fg='white',
                             width=20,
                             relief=tk.FLAT, cursor='hand2')
        clear_btn.pack(pady=2, fill=tk.X)

        # Enhanced scanner button
        scanner_btn = tk.Button(button_frame, text="🔬 Open Scanner",
                               command=self.open_enhanced_scanner,
                               font=('Arial', 11, 'bold'),
                               bg='#e74c3c', fg='white',
                               width=20,
                               relief=tk.FLAT, cursor='hand2')
        scanner_btn.pack(pady=2, fill=tk.X)

    def create_medicine_list(self, parent):
        """Create medicine list with treeview"""
        # Search frame
        search_frame = tk.Frame(parent, bg='#ffffff')
        search_frame.pack(fill=tk.X, padx=15, pady=(15, 5))

        tk.Label(search_frame, text="🔍 Search:", font=('Arial', 11, 'bold'),
                bg='#ffffff', fg='#2c3e50').pack(side=tk.LEFT)

        self.search_entry = tk.Entry(search_frame, font=('Arial', 11), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.search_entry.bind('<KeyRelease>', self.search_medicines)

        refresh_btn = tk.Button(search_frame, text="🔄 Refresh",
                               command=self.load_medicines,
                               font=('Arial', 9, 'bold'),
                               bg='#3498db', fg='white',
                               relief=tk.FLAT, cursor='hand2')
        refresh_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Treeview
        tree_frame = tk.Frame(parent, bg='#ffffff')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        columns = ('ID', 'Name', 'Qty', 'Expiry', 'Batch', 'Category', 'Manufacturer')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)

        # Configure columns
        column_widths = {'ID': 50, 'Name': 200, 'Qty': 60, 'Expiry': 100,
                        'Batch': 100, 'Category': 80, 'Manufacturer': 150}

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100), anchor='center' if col in ['ID', 'Qty'] else 'w')

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind selection
        self.tree.bind('<<TreeviewSelect>>', self.on_medicine_select)

    def open_enhanced_scanner(self):
        """Open the enhanced scanner"""
        try:
            scanner = EnhancedMedicineScannerWithFallback(self.root, callback=self.on_scan_complete)
            scanner.start_scanning()
        except Exception as e:
            messagebox.showerror("Scanner Error", f"Failed to open scanner: {e}")

    def on_scan_complete(self, medicine_data):
        """Handle completed scan data"""
        try:
            # Add to database
            self.add_medicine_to_db(medicine_data)

            # Refresh the list
            self.load_medicines()

            print(f"✓ Medicine added from scan: {medicine_data.get('name', 'Unknown')}")

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add scanned medicine: {e}")

    def add_medicine_manual(self):
        """Add medicine from manual form entry"""
        try:
            # Get form data
            medicine_data = {
                'name': self.form_entries['name'].get().strip(),
                'quantity': self.form_entries['quantity'].get().strip() or '0',
                'expiry_date': self.form_entries['expiry'].get().strip(),
                'batch_number': self.form_entries['batch'].get().strip(),
                'manufacturer': self.form_entries['manufacturer'].get().strip(),
                'category': self.category_var.get(),
                'notes': self.notes_text.get(1.0, tk.END).strip(),
                'source': 'manual_form'
            }

            # Validate required fields
            if not medicine_data['name']:
                messagebox.showerror("Error", "Medicine name is required!")
                return

            try:
                quantity = int(medicine_data['quantity'])
                if quantity < 0:
                    raise ValueError("Quantity cannot be negative")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid quantity (number)")
                return

            # Validate date format if provided
            if medicine_data['expiry_date']:
                try:
                    datetime.strptime(medicine_data['expiry_date'], '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Error", "Please enter expiry date in YYYY-MM-DD format")
                    return

            # Add to database
            self.add_medicine_to_db(medicine_data)

            # Clear form and refresh list
            self.clear_form()
            self.load_medicines()

            messagebox.showinfo("Success", f"Medicine '{medicine_data['name']}' added successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add medicine: {e}")

    def add_medicine_to_db(self, medicine_data):
        """Add medicine data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO medicines 
                (user_id, name, quantity, expiry_date, batch_number, manufacturer, category, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.current_user_id,
                medicine_data.get('name', ''),
                int(medicine_data.get('quantity', 0)),
                medicine_data.get('expiry_date') or None,
                medicine_data.get('batch_number') or None,
                medicine_data.get('manufacturer') or None,
                medicine_data.get('category', 'Other'),
                medicine_data.get('notes', '')
            ))

            conn.commit()
            conn.close()

            print(f"✓ Medicine added to database: {medicine_data.get('name')}")

        except Exception as e:
            print(f"Database error: {e}")
            raise e

    def load_medicines(self):
        """Load medicines from database"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, name, quantity, expiry_date, batch_number, category, manufacturer
                FROM medicines 
                WHERE user_id = ?
                ORDER BY name ASC
            ''', (self.current_user_id,))

            medicines = cursor.fetchall()
            conn.close()

            # Add items to tree
            for medicine in medicines:
                med_id, name, qty, expiry, batch, category, manufacturer = medicine

                # Format display values
                expiry_display = expiry if expiry else 'N/A'
                batch_display = batch if batch else 'N/A'
                manufacturer_display = manufacturer if manufacturer else 'N/A'

                self.tree.insert('', tk.END, values=(
                    med_id, name, qty, expiry_display,
                    batch_display, category, manufacturer_display
                ))

            print(f"✓ Loaded {len(medicines)} medicines")

        except Exception as e:
            print(f"Error loading medicines: {e}")
            messagebox.showerror("Database Error", f"Failed to load medicines: {e}")

    def search_medicines(self, event=None):
        """Search medicines based on name"""
        search_term = self.search_entry.get().lower()

        if not search_term:
            self.load_medicines()
            return

        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, name, quantity, expiry_date, batch_number, category, manufacturer
                FROM medicines 
                WHERE user_id = ? AND (
                    LOWER(name) LIKE ? OR 
                    LOWER(manufacturer) LIKE ? OR 
                    LOWER(batch_number) LIKE ?
                )
                ORDER BY name ASC
            ''', (self.current_user_id, f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))

            medicines = cursor.fetchall()
            conn.close()

            # Add filtered items to tree
            for medicine in medicines:
                med_id, name, qty, expiry, batch, category, manufacturer = medicine

                expiry_display = expiry if expiry else 'N/A'
                batch_display = batch if batch else 'N/A'
                manufacturer_display = manufacturer if manufacturer else 'N/A'

                self.tree.insert('', tk.END, values=(
                    med_id, name, qty, expiry_display,
                    batch_display, category, manufacturer_display
                ))

        except Exception as e:
            print(f"Search error: {e}")

    def on_medicine_select(self, event):
        """Handle medicine selection in tree"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item)['values']

            try:
                # Get full medicine data
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT name, quantity, expiry_date, batch_number, manufacturer, category, description
                    FROM medicines WHERE id = ?
                ''', (values[0],))

                medicine = cursor.fetchone()
                conn.close()

                if medicine:
                    name, qty, expiry, batch, manufacturer, category, description = medicine

                    # Populate form fields for editing
                    self.clear_form()
                    self.form_entries['name'].insert(0, name)
                    self.form_entries['quantity'].insert(0, str(qty))
                    if expiry:
                        self.form_entries['expiry'].insert(0, expiry)
                    if batch:
                        self.form_entries['batch'].insert(0, batch)
                    if manufacturer:
                        self.form_entries['manufacturer'].insert(0, manufacturer)
                    self.category_var.set(category or 'Other')
                    if description:
                        self.notes_text.insert(1.0, description)

            except Exception as e:
                print(f"Error loading medicine details: {e}")

    def clear_form(self):
        """Clear all form fields"""
        for entry in self.form_entries.values():
            entry.delete(0, tk.END)
        self.category_var.set('Tablet')
        self.notes_text.delete(1.0, tk.END)

    def run(self):
        """Start the application"""
        print("🚀 Starting MediSort Pro...")
        print(f"📊 ML Available: {ML_AVAILABLE}")
        print("💡 Use the Smart Scanner for automatic detection or manual entry form")
        self.root.mainloop()


# Enhanced main application with integrated scanner
def create_usage_example():
    """
    Example of how to integrate both manual and auto-scan functionality
    """

    # Create the enhanced application
    app = EnhancedMediSortMainApp()

    # Run the application
    app.run()

# Usage example and integration instructions
class MediSortIntegrator:
    """
    Utility class to help integrate the enhanced scanner into existing applications
    """

    @staticmethod
    def create_scanner_widget(parent, callback=None):
        """
        Create a scanner widget that can be embedded in existing applications
        """
        frame = tk.Frame(parent, bg='#f8f9fa', relief=tk.RAISED, bd=2)

        # Title
        title = tk.Label(frame, text="🔬 Smart Medicine Scanner",
                        font=('Arial', 14, 'bold'),
                        bg='#f8f9fa', fg='#2c3e50')
        title.pack(pady=10)

        # Scanner button
        scanner_btn = tk.Button(frame, text="📷 Open Scanner",
                               command=lambda: MediSortIntegrator.open_scanner(parent, callback),
                               font=('Arial', 12, 'bold'),
                               bg='#e74c3c', fg='white',
                               width=20, height=2,
                               relief=tk.FLAT, cursor='hand2')
        scanner_btn.pack(pady=10)

        # Status
        status = tk.Label(frame,
                         text=f"Status: {'AI Ready' if ML_AVAILABLE else 'Traditional OCR'}",
                         font=('Arial', 10),
                         bg='#f8f9fa',
                         fg='#27ae60' if ML_AVAILABLE else '#f39c12')
        status.pack(pady=(0, 10))

        return frame

    @staticmethod
    def open_scanner(parent, callback=None):
        """
        Open the enhanced scanner with callback
        """
        try:
            scanner = EnhancedMedicineScannerWithFallback(parent, callback=callback)
            scanner.start_scanning()
        except Exception as e:
            messagebox.showerror("Scanner Error", f"Failed to open scanner: {e}")

    @staticmethod
    def get_scanner_capabilities():
        """
        Get information about scanner capabilities
        """
        return {
            'ml_available': ML_AVAILABLE,
            'ocr_methods': ['Tesseract'] + (['EasyOCR'] if ML_AVAILABLE else []),
            'scan_modes': ['manual', 'auto_detect', 'dual_mode'],
            'supported_formats': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif'],
            'extraction_fields': [
                'medicine_name', 'quantity', 'expiry_date',
                'batch_number', 'manufacturer', 'category'
            ]
        }


# Utility functions for easy integration
class ScannerConfig:
    """
    Configuration class for customizing scanner behavior
    """

    def __init__(self):
        # OCR Settings
        self.ocr_confidence_threshold = 0.3
        self.tesseract_config = '--psm 6'  # Assume single column text

        # Auto-detection settings
        self.auto_detect_interval = 2000  # milliseconds
        self.text_region_min_area = 100
        self.text_region_max_area = 5000
        self.min_text_regions_for_detection = 3

        # UI Settings
        self.camera_resolution = (1280, 720)
        self.display_resolution = (640, 400)
        self.scan_result_display_limit = 10

        # Data validation
        self.required_fields = ['name']
        self.date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']

        # File settings
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        self.max_file_size_mb = 10

    def update_settings(self, **kwargs):
        """Update configuration settings"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: Unknown setting '{key}'")


# Configuration class for easy customization
if __name__ == "__main__":
    """
    Main execution - demonstrates both manual and auto-scan integration
    """

    print("=" * 60)
    print("🏥 MEDISORT PRO - SMART MEDICINE INVENTORY SYSTEM")
    print("=" * 60)
    print()
    print("Features:")
    print("✓ Manual medicine entry")
    print("✓ Smart camera scanning")
    print("✓ Auto-detection mode")
    print("✓ Dual mode operation")
    print("✓ File-based scanning")
    print("✓ Advanced text recognition")
    if ML_AVAILABLE:
        print("✓ AI-powered extraction")
    print("✓ Data validation")
    print("✓ Export/import capabilities")
    print()
    print("=" * 60)

    try:
        # Create and run the application
        create_usage_example()
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        print("Please check your dependencies and try again.")
        input("Press Enter to exit...")


# Main execution


























































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































class EnhancedMedicineScannerWithFallback:
    """
    Enhanced medicine scanner that combines ML detection with traditional OCR fallback
    """

    def __init__(self, parent, callback=None):
        self.parent = parent
        self.callback = callback
        self.cap = None
        self.scanning = False
        self.scan_window = None
        self.auto_scan_mode = True
        self.last_scan_result = None

        # Initialize OCR readers
        self.init_ocr_readers()

    def init_ocr_readers(self):
        """Initialize OCR readers based on available libraries"""
        self.ocr_reader = None
        self.use_easyocr = False

        if ML_AVAILABLE:
            try:
                self.ocr_reader = easyocr.Reader(['en'])
                self.use_easyocr = True
                print("✓ EasyOCR initialized")
            except Exception as e:
                print(f"⚠ EasyOCR initialization failed: {e}")
                self.use_easyocr = False

    def start_scanning(self):
        """Start the enhanced scanning interface"""
        self.scan_window = tk.Toplevel(self.parent)
        self.scan_window.title("Enhanced Medicine Scanner - Manual & Auto Detection")
        self.scan_window.geometry("1000x900")
        self.scan_window.configure(bg='#f0f8ff')

        # Center the window
        self.center_window()

        # Create the scanner interface
        self.create_scanner_interface()

        # Start camera
        self.start_camera()

    def center_window(self):
        """Center the scan window"""
        self.scan_window.update_idletasks()
        width = self.scan_window.winfo_width()
        height = self.scan_window.winfo_height()
        x = (self.scan_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.scan_window.winfo_screenheight() // 2) - (height // 2)
        self.scan_window.geometry(f'{width}x{height}+{x}+{y}')

    def create_scanner_interface(self):
        """Create the complete scanner interface"""
        # Title section
        self.create_title_section()

        # Scanner mode selection
        self.create_mode_selection()

        # Camera display
        self.create_camera_section()

        # Control buttons
        self.create_control_section()

        # Results and manual entry section
        self.create_results_section()

        # Action buttons
        self.create_action_section()

    def create_title_section(self):
        """Create title and status section"""
        title_frame = tk.Frame(self.scan_window, bg='#f0f8ff')
        title_frame.pack(pady=15, fill=tk.X)

        # Main title
        title_label = tk.Label(title_frame,
                              text="🔬 Smart Medicine Scanner",
                              font=('Arial', 20, 'bold'),
                              bg='#f0f8ff', fg='#2c3e50')
        title_label.pack()

        # Subtitle with capabilities
        capabilities = "Manual Entry • Auto-Detection • Dual Mode Operation"
        if ML_AVAILABLE:
            capabilities += " • AI Enhanced"

        subtitle = tk.Label(title_frame,
                           text=capabilities,
                           font=('Arial', 11),
                           bg='#f0f8ff', fg='#7f8c8d')
        subtitle.pack(pady=(5, 0))

        # Status indicator
        status_color = "#27ae60" if ML_AVAILABLE else "#f39c12"
        status_text = "AI Ready" if ML_AVAILABLE else "Traditional OCR"

        status_label = tk.Label(title_frame,
                               text=f"Status: {status_text}",
                               font=('Arial', 10, 'bold'),
                               bg='#f0f8ff', fg=status_color)
        status_label.pack(pady=(2, 0))

    def create_mode_selection(self):
        """Create scanning mode selection"""
        mode_frame = tk.LabelFrame(self.scan_window,
                                  text="📋 Scanning Mode",
                                  font=('Arial', 12, 'bold'),
                                  bg='#f0f8ff', fg='#2c3e50')
        mode_frame.pack(pady=10, padx=20, fill=tk.X)

        # Mode selection buttons
        button_frame = tk.Frame(mode_frame, bg='#f0f8ff')
        button_frame.pack(pady=10)

        # Auto-scan mode
        self.auto_mode_btn = tk.Button(button_frame,
                                      text="🔄 Auto-Detect Mode",
                                      command=lambda: self.set_scan_mode(True),
                                      font=('Arial', 11, 'bold'),
                                      bg='#3498db', fg='white',
                                      width=18, height=2,
                                      relief=tk.FLAT, cursor='hand2')
        self.auto_mode_btn.pack(side=tk.LEFT, padx=5)

        # Manual mode
        self.manual_mode_btn = tk.Button(button_frame,
                                        text="✋ Manual Mode",
                                        command=lambda: self.set_scan_mode(False),
                                        font=('Arial', 11, 'bold'),
                                        bg='#95a5a6', fg='white',
                                        width=18, height=2,
                                        relief=tk.FLAT, cursor='hand2')
        self.manual_mode_btn.pack(side=tk.LEFT, padx=5)

        # Dual mode (both)
        self.dual_mode_btn = tk.Button(button_frame,
                                      text="⚡ Dual Mode",
                                      command=lambda: self.set_scan_mode("dual"),
                                      font=('Arial', 11, 'bold'),
                                      bg='#e74c3c', fg='white',
                                      width=18, height=2,
                                      relief=tk.FLAT, cursor='hand2')
        self.dual_mode_btn.pack(side=tk.LEFT, padx=5)

        # Instructions
        instructions = tk.Label(mode_frame,
                               text="Auto-Detect: Continuous scanning • Manual: Click to capture • Dual: Both modes active",
                               font=('Arial', 9),
                               bg='#f0f8ff', fg='#7f8c8d',
                               wraplength=800)
        instructions.pack(pady=(0, 10))

    def create_camera_section(self):
        """Create camera display section"""
        camera_container = tk.LabelFrame(self.scan_window,
                                        text="📹 Camera Feed",
                                        font=('Arial', 12, 'bold'),
                                        bg='#f0f8ff', fg='#2c3e50')
        camera_container.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Camera frame with detection overlay
        self.camera_frame = tk.Label(camera_container,
                                    text="🎥 Initializing camera...\n\nPlease wait while we connect to your camera",
                                    bg='#34495e', fg='white',
                                    font=('Arial', 14),
                                    width=70, height=15)
        self.camera_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Detection status
        self.detection_status = tk.Label(camera_container,
                                        text="Detection Status: Standby",
                                        font=('Arial', 10, 'bold'),
                                        bg='#f0f8ff', fg='#7f8c8d')
        self.detection_status.pack(pady=(0, 10))

    def create_control_section(self):
        """Create control buttons section"""
        control_frame = tk.Frame(self.scan_window, bg='#f0f8ff')
        control_frame.pack(pady=10)

        # Capture button (for manual mode)
        self.capture_btn = tk.Button(control_frame,
                                    text="📷 Capture Image",
                                    command=self.manual_capture,
                                    font=('Arial', 12, 'bold'),
                                    bg='#e74c3c', fg='white',
                                    width=15, height=2,
                                    relief=tk.FLAT, cursor='hand2')
        self.capture_btn.pack(side=tk.LEFT, padx=5)

        # File scan button
        self.file_btn = tk.Button(control_frame,
                                 text="📁 Scan from File",
                                 command=self.scan_from_file,
                                 font=('Arial', 12, 'bold'),
                                 bg='#3498db', fg='white',
                                 width=15, height=2,
                                 relief=tk.FLAT, cursor='hand2')
        self.file_btn.pack(side=tk.LEFT, padx=5)

        # Clear results button
        self.clear_btn = tk.Button(control_frame,
                                  text="🧹 Clear Results",
                                  command=self.clear_results,
                                  font=('Arial', 12, 'bold'),
                                  bg='#95a5a6', fg='white',
                                  width=15, height=2,
                                  relief=tk.FLAT, cursor='hand2')
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Close button
        self.close_btn = tk.Button(control_frame,
                                  text="❌ Close",
                                  command=self.close_scanner,
                                  font=('Arial', 12, 'bold'),
                                  bg='#e67e22', fg='white',
                                  width=15, height=2,
                                  relief=tk.FLAT, cursor='hand2')
        self.close_btn.pack(side=tk.LEFT, padx=5)

    def create_results_section(self):
        """Create results display and manual entry section"""
        results_container = tk.Frame(self.scan_window, bg='#f0f8ff')
        results_container.pack(pady=10, padx=20, fill=tk.X)

        # Left side - Scan results
        scan_results_frame = tk.LabelFrame(results_container,
                                          text="🔍 Scan Results",
                                          font=('Arial', 12, 'bold'),
                                          bg='#f0f8ff', fg='#2c3e50')
        scan_results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Results text area
        results_frame = tk.Frame(scan_results_frame, bg='#ffffff')
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        self.results_text = tk.Text(results_frame,
                                   height=8, width=40,
                                   font=('Courier', 9),
                                   bg='#ffffff', fg='#2c3e50',
                                   wrap=tk.WORD)

        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL,
                                         command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right side - Manual entry/editing
        manual_entry_frame = tk.LabelFrame(results_container,
                                          text="✏️ Manual Entry/Edit",
                                          font=('Arial', 12, 'bold'),
                                          bg='#f0f8ff', fg='#2c3e50')
        manual_entry_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Manual entry fields
        self.create_manual_entry_fields(manual_entry_frame)

    def create_manual_entry_fields(self, parent):
        """Create manual entry fields"""
        fields_frame = tk.Frame(parent, bg='#ffffff')
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        # Medicine name
        tk.Label(fields_frame, text="Medicine Name:", font=('Arial', 9, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.name_entry = tk.Entry(fields_frame, font=('Arial', 9), width=25)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2, sticky='ew')

        # Quantity
        tk.Label(fields_frame, text="Quantity:", font=('Arial', 9, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.quantity_entry = tk.Entry(fields_frame, font=('Arial', 9), width=25)
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=2, sticky='ew')

        # Expiry date
        tk.Label(fields_frame, text="Expiry Date:", font=('Arial', 9, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.expiry_entry = tk.Entry(fields_frame, font=('Arial', 9), width=25)
        self.expiry_entry.grid(row=2, column=1, padx=5, pady=2, sticky='ew')

        # Batch number
        tk.Label(fields_frame, text="Batch Number:", font=('Arial', 9, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.batch_entry = tk.Entry(fields_frame, font=('Arial', 9), width=25)
        self.batch_entry.grid(row=3, column=1, padx=5, pady=2, sticky='ew')

        # Manufacturer
        tk.Label(fields_frame, text="Manufacturer:", font=('Arial', 9, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.manufacturer_entry = tk.Entry(fields_frame, font=('Arial', 9), width=25)
        self.manufacturer_entry.grid(row=4, column=1, padx=5, pady=2, sticky='ew')

        # Category
        tk.Label(fields_frame, text="Category:", font=('Arial', 9, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=5, column=0, sticky='w', padx=5, pady=2)
        self.category_var = tk.StringVar(value='Tablet')
        self.category_combo = ttk.Combobox(fields_frame, textvariable=self.category_var,
                                          values=['Tablet', 'Capsule', 'Syrup', 'Injection',
                                                 'Cream', 'Drops', 'Other'],
                                          font=('Arial', 9), width=22)
        self.category_combo.grid(row=5, column=1, padx=5, pady=2, sticky='ew')

        # Notes/Description
        tk.Label(fields_frame, text="Notes:", font=('Arial', 9, 'bold'),
                bg='#ffffff', fg='#2c3e50').grid(row=6, column=0, sticky='nw', padx=5, pady=2)
        self.notes_text = tk.Text(fields_frame, font=('Arial', 8), width=25, height=3)
        self.notes_text.grid(row=6, column=1, padx=5, pady=2, sticky='ew')

        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)

        # Copy from scan button
        copy_frame = tk.Frame(fields_frame, bg='#ffffff')
        copy_frame.grid(row=7, column=0, columnspan=2, pady=10, sticky='ew')

        tk.Button(copy_frame, text="📋 Copy from Scan",
                 command=self.copy_from_scan,
                 font=('Arial', 9, 'bold'),
                 bg='#27ae60', fg='white',
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=2)

        tk.Button(copy_frame, text="🧹 Clear Fields",
                 command=self.clear_manual_fields,
                 font=('Arial', 9, 'bold'),
                 bg='#95a5a6', fg='white',
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=2)

    def create_action_section(self):
        """Create final action buttons"""
        action_frame = tk.Frame(self.scan_window, bg='#f0f8ff')
        action_frame.pack(pady=15)

        # Add to inventory button
        self.add_btn = tk.Button(action_frame,
                                text="➕ Add to Inventory",
                                command=self.add_to_inventory,
                                font=('Arial', 14, 'bold'),
                                bg='#27ae60', fg='white',
                                width=20, height=2,
                                relief=tk.FLAT, cursor='hand2',
                                state=tk.DISABLED)
        self.add_btn.pack(side=tk.LEFT, padx=10)

        # Save scan results button
        self.save_scan_btn = tk.Button(action_frame,
                                      text="💾 Save Scan Results",
                                      command=self.save_scan_results,
                                      font=('Arial', 14, 'bold'),
                                      bg='#3498db', fg='white',
                                      width=20, height=2,
                                      relief=tk.FLAT, cursor='hand2')
        self.save_scan_btn.pack(side=tk.LEFT, padx=10)

    def set_scan_mode(self, mode):
        """Set scanning mode (True=auto, False=manual, 'dual'=both)"""
        self.auto_scan_mode = mode

        # Update button appearance
        self.auto_mode_btn.configure(bg='#95a5a6')
        self.manual_mode_btn.configure(bg='#95a5a6')
        self.dual_mode_btn.configure(bg='#95a5a6')

        if mode is True:
            self.auto_mode_btn.configure(bg='#3498db')
            self.detection_status.configure(text="Detection Status: Auto-Detect Active", fg='#27ae60')
        elif mode is False:
            self.manual_mode_btn.configure(bg='#3498db')
            self.detection_status.configure(text="Detection Status: Manual Mode", fg='#f39c12')
        else:  # dual mode
            self.dual_mode_btn.configure(bg='#e74c3c')
            self.detection_status.configure(text="Detection Status: Dual Mode Active", fg='#e74c3c')

    def start_camera(self):
        """Start camera feed"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Cannot open camera")

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            self.scanning = True
            self.update_camera_feed()

        except Exception as e:
            print(f"Camera error: {e}")
            self.camera_frame.configure(
                text=f"❌ Camera Error\n\n{str(e)}\n\nYou can still use 'Scan from File' option",
                fg='#e74c3c'
            )

    def update_camera_feed(self):
        """Update camera feed with detection overlay"""
        if self.scanning and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                display_frame = frame.copy()

                # Auto-detection in dual or auto mode
                if self.auto_scan_mode in [True, "dual"]:
                    try:
                        # Run detection in background
                        threading.Thread(target=self.auto_detect_background,
                                       args=(frame.copy(),), daemon=True).start()

                        # Add detection overlay
                        cv2.putText(display_frame, "AUTO-DETECT ON", (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    except Exception as e:
                        print(f"Auto-detection error: {e}")

                # Manual mode overlay
                if self.auto_scan_mode in [False, "dual"]:
                    cv2.putText(display_frame, "MANUAL MODE", (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 2)

                # Resize and convert for display
                display_frame = cv2.resize(display_frame, (640, 400))
                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)

                # Convert to PhotoImage
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(img)

                # Update display
                self.camera_frame.configure(image=img_tk)
                self.camera_frame.image = img_tk

            # Schedule next update
            if self.scan_window and self.scan_window.winfo_exists():
                self.scan_window.after(33, self.update_camera_feed)  # ~30 FPS

    def auto_detect_background(self, frame):
        """Background auto-detection (non-blocking)"""
        try:
            # Simple text detection to trigger processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Use edge detection to find potential text regions
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter contours that might contain text
            text_regions = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                area = cv2.contourArea(contour)

                # Potential text region criteria
                if 100 < area < 5000 and 1.5 < aspect_ratio < 10:
                    text_regions += 1

            # If sufficient text regions detected, process the image
            if text_regions >= 3:  # Threshold for medicine strip detection
                self.process_detected_frame(frame)

        except Exception as e:
            print(f"Auto-detection background error: {e}")

    def process_detected_frame(self, frame):
        """Process detected frame for medicine information"""
        try:
            # Extract text using available OCR
            extracted_info = self.extract_medicine_info(frame)

            if extracted_info and any(extracted_info.values()):
                # Update UI in main thread
                self.scan_window.after(0, self.update_scan_results, extracted_info)

        except Exception as e:
            print(f"Frame processing error: {e}")

    def manual_capture(self):
        """Manual capture from camera"""
        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Error", "Camera not available")
            return

        # Capture frame
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture image")
            return

        # Show processing message
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "📷 Processing captured image...\n\n")

        # Process in separate thread
        threading.Thread(target=self.process_captured_frame,
                        args=(frame,), daemon=True).start()

    def process_captured_frame(self, frame):
        """Process manually captured frame"""
        try:
            extracted_info = self.extract_medicine_info(frame)
            # Update UI in main thread
            self.scan_window.after(0, self.update_scan_results, extracted_info)

        except Exception as e:
            error_msg = f"❌ Processing failed: {str(e)}\n\n"
            self.scan_window.after(0, lambda: (
                self.results_text.delete(1.0, tk.END),
                self.results_text.insert(tk.END, error_msg)
            ))

    def scan_from_file(self):
        """Scan medicine from image file"""
        filetypes = [
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.tiff *.gif'),
            ('All files', '*.*')
        ]

        filename = filedialog.askopenfilename(
            title="Select medicine strip image",
            filetypes=filetypes
        )

        if filename:
            try:
                # Load image
                image = cv2.imread(filename)
                if image is None:
                    raise Exception("Could not load image file")

                # Show processing message
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"📁 Processing file: {os.path.basename(filename)}\n\n")

                # Process in separate thread
                threading.Thread(target=self.process_captured_frame,
                                args=(image,), daemon=True).start()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to process image file: {e}")

    def extract_medicine_info(self, image):
        """Extract medicine information using available OCR methods"""
        extracted_info = {
            'name': '',
            'quantity': '',
            'expiry_date': '',
            'batch_number': '',
            'manufacturer': '',
            'confidence': 0.0,
            'raw_text': []
        }

        try:
            # Method 1: EasyOCR (if available)
            if self.use_easyocr and self.ocr_reader:
                try:
                    results = self.ocr_reader.readtext(image)
                    texts = [(result[1], result[2]) for result in results if result[2] > 0.3]
                    extracted_info['raw_text'].extend([text for text, conf in texts])
                    extracted_info['confidence'] = sum(conf for _, conf in texts) / len(texts) if texts else 0

                    # Parse extracted text
                    all_text = ' '.join([text for text, _ in texts])
                    parsed_info = self.parse_medicine_text(all_text)
                    extracted_info.update(parsed_info)

                    print(f"✓ EasyOCR extraction: {len(texts)} text items found")

                except Exception as e:
                    print(f"EasyOCR failed: {e}")

            # Method 2: Tesseract OCR (fallback)
            if not extracted_info['raw_text']:  # If EasyOCR didn't work
                try:
                    # Preprocess image for better OCR
                    processed_image = self.preprocess_image(image)
                    text = pytesseract.image_to_string(processed_image)

                    if text.strip():
                        extracted_info['raw_text'] = [line.strip() for line in text.split('\n') if line.strip()]
                        extracted_info['confidence'] = 0.7  # Assume moderate confidence

                        # Parse extracted text
                        parsed_info = self.parse_medicine_text(text)
                        extracted_info.update(parsed_info)

                        print(f"✓ Tesseract extraction: {len(extracted_info['raw_text'])} lines found")

                except Exception as e:
                    print(f"Tesseract failed: {e}")

            # Method 3: Basic image analysis (last resort)
            if not extracted_info['raw_text']:
                extracted_info['raw_text'] = ["No text detected - please try manual entry"]
                extracted_info['confidence'] = 0.0

        except Exception as e:
            print(f"OCR extraction failed: {e}")
            extracted_info['raw_text'] = [f"Extraction error: {str(e)}"]

        return extracted_info

    def preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Apply different preprocessing techniques
            # Method 1: Gaussian blur + threshold
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            # Method 2: Morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)

            # Method 3: Resize for better recognition
            height, width = processed.shape
            if width < 1000:
                scale_factor = 1000 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                processed = cv2.resize(processed, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            return processed

        except Exception as e:
            print(f"Image preprocessing failed: {e}")
            return image

    def parse_medicine_text(self, text):
        """Parse medicine information from extracted text"""
        info = {
            'name': '',
            'quantity': '',
            'expiry_date': '',
            'batch_number': '',
            'manufacturer': ''
        }

        if not text:
            return info

        text_upper = text.upper()
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        try:
            # Extract medicine name (usually the first prominent text)
            for line in lines:
                clean_line = line.strip()
                # Skip lines that are clearly not medicine names
                if (len(clean_line) > 3 and
                    not any(keyword in clean_line.upper() for keyword in
                           ['EXP', 'MFG', 'BATCH', 'LOT', 'QTY', 'MG', 'ML']) and
                    not re.match(r'^\d+', clean_line)):
                    info['name'] = clean_line
                    break

            # Extract batch number
            batch_patterns = [
                r'(?:BATCH|LOT|B\.?NO\.?)[:\s]*([A-Z0-9]+)',
                r'B[:\s]*([A-Z0-9]{4,})',
                r'LOT[:\s]*([A-Z0-9]+)',
                r'BATCH[:\s]*([A-Z0-9]+)'
            ]

            for pattern in batch_patterns:
                match = re.search(pattern, text_upper)
                if match:
                    info['batch_number'] = match.group(1)
                    break

            # Extract expiry date
            date_patterns = [
                r'(?:EXP|EXPIRY|EXP\.?\s*DATE)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})',
                r'(\d{2}[/\-\.]\d{4})',  # MM/YYYY format
                r'(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})'  # YYYY/MM/DD format
            ]

            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    raw_date = match.group(1)
                    # Try to standardize date format
                    formatted_date = self.format_date(raw_date)
                    if formatted_date:
                        info['expiry_date'] = formatted_date
                        break

            # Extract quantity
            qty_patterns = [
                r'(\d+)\s*(?:TABLETS?|CAPS?|CAPSULES?)',
                r'QTY[:\s]*(\d+)',
                r'(\d+)\s*(?:PCS?|PIECES?)',
                r'(\d+)\s*(?:TABS?)',
                r'CONTAINS?\s*(\d+)'
            ]

            for pattern in qty_patterns:
                match = re.search(pattern, text_upper)
                if match:
                    info['quantity'] = match.group(1)
                    break

            # Extract manufacturer
            mfg_patterns = [
                r'(?:MFG|MANUFACTURED BY|MFD BY)[:\s]*([A-Z][A-Z\s&\.]+?)(?:\n|$)',
                r'(?:PHARMA|LABORATORIES|LTD|INC)[A-Z\s]*',
                r'BY[:\s]*([A-Z][A-Z\s&\.]+?)(?:\n|$)'
            ]

            for pattern in mfg_patterns:
                match = re.search(pattern, text_upper)
                if match:
                    manufacturer = match.group(1).strip() if match.groups() else match.group(0).strip()
                    if len(manufacturer) > 3:
                        info['manufacturer'] = manufacturer
                        break

        except Exception as e:
            print(f"Text parsing error: {e}")

        return info

    def format_date(self, date_string):
        """Format date string to YYYY-MM-DD"""
        try:
            # Remove extra spaces and normalize separators
            date_string = re.sub(r'[/\-\.]', '-', date_string.strip())

            # Try different date formats
            formats = [
                '%d-%m-%Y',   # DD-MM-YYYY
                '%d-%m-%y',   # DD-MM-YY
                '%m-%d-%Y',   # MM-DD-YYYY
                '%m-%d-%y',   # MM-DD-YY
                '%Y-%m-%d',   # YYYY-MM-DD (already correct)
                '%m-%Y'       # MM-YYYY
            ]

            for fmt in formats:
                try:
                    if fmt == '%m-%Y':  # Handle MM-YYYY case
                        parts = date_string.split('-')
                        if len(parts) == 2:
                            month, year = parts
                            # Assume end of month for expiry
                            return f"{year}-{month:0>2}-28"
                    else:
                        parsed_date = datetime.strptime(date_string, fmt)
                        # Handle 2-digit years
                        if parsed_date.year < 100:
                            parsed_date = parsed_date.replace(year=parsed_date.year + 2000)

                        return parsed_date.strftime('%Y-%m-%d')

                except ValueError:
                    continue

            return date_string  # Return original if no format matches

        except Exception:
            return date_string

    def update_scan_results(self, extracted_info):
        """Update scan results display"""
        try:
            # Clear results
            self.results_text.delete(1.0, tk.END)

            if extracted_info:
                confidence = extracted_info.get('confidence', 0)

                # Show extraction results
                self.results_text.insert(tk.END, "🔍 SCAN RESULTS\n")
                self.results_text.insert(tk.END, "=" * 30 + "\n\n")

                if confidence > 0:
                    self.results_text.insert(tk.END, f"📊 Confidence: {confidence:.1%}\n\n")

                # Show parsed information
                fields = [
                    ('Medicine Name', extracted_info.get('name', '')),
                    ('Quantity', extracted_info.get('quantity', '')),
                    ('Expiry Date', extracted_info.get('expiry_date', '')),
                    ('Batch Number', extracted_info.get('batch_number', '')),
                    ('Manufacturer', extracted_info.get('manufacturer', ''))
                ]

                found_any = False
                for field_name, value in fields:
                    if value:
                        self.results_text.insert(tk.END, f"📋 {field_name}: {value}\n")
                        found_any = True

                if not found_any:
                    self.results_text.insert(tk.END, "⚠️ No structured data extracted\n")

                # Show raw text
                raw_text = extracted_info.get('raw_text', [])
                if raw_text:
                    self.results_text.insert(tk.END, f"\n📝 Raw Text ({len(raw_text)} items):\n")
                    self.results_text.insert(tk.END, "-" * 25 + "\n")

                    for i, text in enumerate(raw_text[:10], 1):  # Show first 10 items
                        self.results_text.insert(tk.END, f"{i:2}. {text}\n")

                    if len(raw_text) > 10:
                        self.results_text.insert(tk.END, f"... and {len(raw_text) - 10} more items\n")

                # Store results for copying
                self.last_scan_result = extracted_info

                # Enable add button if good results
                if confidence > 0.3 and extracted_info.get('name'):
                    self.add_btn.configure(state=tk.NORMAL)
                else:
                    self.add_btn.configure(state=tk.DISABLED)

            else:
                self.results_text.insert(tk.END, "❌ No information extracted\n")
                self.results_text.insert(tk.END, "💡 Try adjusting camera angle or lighting\n")
                self.add_btn.configure(state=tk.DISABLED)

        except Exception as e:
            print(f"Error updating scan results: {e}")

    def copy_from_scan(self):
        """Copy scan results to manual entry fields"""
        if not self.last_scan_result:
            messagebox.showwarning("No Data", "No scan results available to copy")
            return

        try:
            # Clear existing fields
            self.clear_manual_fields()

            # Copy data
            if self.last_scan_result.get('name'):
                self.name_entry.insert(0, self.last_scan_result['name'])

            if self.last_scan_result.get('quantity'):
                self.quantity_entry.insert(0, self.last_scan_result['quantity'])

            if self.last_scan_result.get('expiry_date'):
                self.expiry_entry.insert(0, self.last_scan_result['expiry_date'])

            if self.last_scan_result.get('batch_number'):
                self.batch_entry.insert(0, self.last_scan_result['batch_number'])

            if self.last_scan_result.get('manufacturer'):
                self.manufacturer_entry.insert(0, self.last_scan_result['manufacturer'])

            # Add scan info to notes
            confidence = self.last_scan_result.get('confidence', 0)
            notes = f"Scan confidence: {confidence:.1%}\nAuto-extracted on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.notes_text.insert(1.0, notes)

            # Enable add button
            self.add_btn.configure(state=tk.NORMAL)

            messagebox.showinfo("Success", "Scan results copied to manual entry fields!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy scan results: {e}")

    def clear_manual_fields(self):
        """Clear all manual entry fields"""
        self.name_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.expiry_entry.delete(0, tk.END)
        self.batch_entry.delete(0, tk.END)
        self.manufacturer_entry.delete(0, tk.END)
        self.notes_text.delete(1.0, tk.END)

    def clear_results(self):
        """Clear scan results and manual fields"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Results cleared. Ready for new scan.\n")
        self.clear_manual_fields()
        self.last_scan_result = None
        self.add_btn.configure(state=tk.DISABLED)

    def get_manual_entry_data(self):
        """Get data from manual entry fields"""
        return {
            'name': self.name_entry.get().strip(),
            'quantity': self.quantity_entry.get().strip(),
            'expiry_date': self.expiry_entry.get().strip(),
            'batch_number': self.batch_entry.get().strip(),
            'manufacturer': self.manufacturer_entry.get().strip(),
            'category': self.category_var.get(),
            'notes': self.notes_text.get(1.0, tk.END).strip(),
            'source': 'manual_entry'
        }

    def validate_entry_data(self, data):
        """Validate entry data before adding to inventory"""
        errors = []

        if not data['name']:
            errors.append("Medicine name is required")

        if data['quantity'] and not data['quantity'].isdigit():
            errors.append("Quantity must be a number")

        if data['expiry_date']:
            try:
                datetime.strptime(data['expiry_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Expiry date must be in YYYY-MM-DD format")

        return errors

    def add_to_inventory(self):
        """Add medicine to inventory"""
        # Get data from manual fields (which might contain scan data)
        medicine_data = self.get_manual_entry_data()

        # Validate data
        errors = self.validate_entry_data(medicine_data)
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        # Call parent callback if available
        if self.callback:
            try:
                self.callback(medicine_data)
                messagebox.showinfo("Success", "Medicine added to inventory!")

                # Clear fields for next entry
                self.clear_manual_fields()
                self.clear_results()

                # Ask if user wants to continue scanning
                continue_scan = messagebox.askyesno("Continue?",
                                                   "Medicine added successfully!\n\nContinue scanning more medicines?")
                if not continue_scan:
                    self.close_scanner()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add medicine: {e}")
        else:
            messagebox.showwarning("No Callback", "No inventory callback configured")

    def save_scan_results(self):
        """Save scan results to file"""
        if not self.last_scan_result:
            messagebox.showwarning("No Data", "No scan results to save")
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension='.json',
                filetypes=[
                    ('JSON files', '*.json'),
                    ('Text files', '*.txt'),
                    ('All files', '*.*')
                ],
                title="Save scan results"
            )

            if filename:
                # Add metadata
                save_data = {
                    'timestamp': datetime.now().isoformat(),
                    'scan_results': self.last_scan_result,
                    'manual_entry': self.get_manual_entry_data(),
                    'scanner_mode': self.auto_scan_mode,
                    'ml_available': ML_AVAILABLE
                }

                # Save based on file extension
                if filename.lower().endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(save_data, f, indent=2, ensure_ascii=False)
                else:
                    # Save as text file
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write("MEDICINE SCAN RESULTS\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Timestamp: {save_data['timestamp']}\n")
                        f.write(f"Scanner Mode: {save_data['scanner_mode']}\n")
                        f.write(f"ML Available: {save_data['ml_available']}\n\n")

                        f.write("EXTRACTED INFORMATION:\n")
                        f.write("-" * 25 + "\n")
                        for key, value in self.last_scan_result.items():
                            if key != 'raw_text' and value:
                                f.write(f"{key.replace('_', ' ').title()}: {value}\n")

                        f.write("\nRAW TEXT:\n")
                        f.write("-" * 10 + "\n")
                        for text in self.last_scan_result.get('raw_text', []):
                            f.write(f"- {text}\n")

                messagebox.showinfo("Success", f"Scan results saved to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {e}")

    def close_scanner(self):
        """Close the scanner window"""
        self.scanning = False
        if self.cap:
            self.cap.release()
        if self.scan_window:
            self.scan_window.destroy()
