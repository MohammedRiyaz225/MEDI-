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
from auth import AuthManager
from inventory import InventoryManager
from logic.db_handler import DatabaseManager

# Import ML components
try:
    from ml_medicine_scanner import MLMedicineScanner, MLTrainingInterface, MLModelManager
    ML_AVAILABLE = True
except ImportError as e:
    print(f"ML components not available: {e}")
    ML_AVAILABLE = False


class EnhancedMediSortApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MediSort - AI-Powered Medicine Inventory Manager")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        self.center_window()

        # Initialize components
        self.db_manager = DatabaseManager()
        self.auth = AuthManager(self.db_manager)
        self.current_user_id = None
        self.current_username = None

        # ML components
        if ML_AVAILABLE:
            self.ml_manager = MLModelManager()
            self.ml_training_interface = None

        self.create_main_interface()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_main_interface(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.main_frame = tk.Frame(self.root, bg='#34495e')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Enhanced title with ML indicator
        title_frame = tk.Frame(self.main_frame, bg='#34495e')
        title_frame.pack(pady=50)

        main_title = tk.Label(title_frame, text="🏥 MediSort",
                             font=('Arial', 36, 'bold'), fg='#ecf0f1', bg='#34495e')
        main_title.pack()

        subtitle = tk.Label(title_frame, text="AI-Powered Smart Medicine Inventory Manager",
                           font=('Arial', 14), fg='#bdc3c7', bg='#34495e')
        subtitle.pack(pady=5)

        # ML status indicator
        if ML_AVAILABLE:
            ml_status = tk.Label(title_frame, text="🤖 Machine Learning Ready",
                                font=('Arial', 10, 'bold'), fg='#2ecc71', bg='#34495e')
            ml_status.pack(pady=5)

        container = tk.Frame(self.main_frame, bg='#2c3e50', padx=40, pady=30)
        container.pack(pady=30)

        self.build_login(container)
        self.build_register(container)

        # Add ML features info
        if ML_AVAILABLE:
            self.build_ml_features_info(container)

        self.root.bind('<Return>', lambda event: self.login_user())

    def build_login(self, container):
        frame = tk.LabelFrame(container, text="Login", font=('Arial', 14, 'bold'),
                              fg='#3498db', bg='#2c3e50', padx=20, pady=20)
        frame.grid(row=0, column=0, padx=20, pady=10)

        tk.Label(frame, text="Username:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=0, column=0, sticky='w', pady=5)
        self.login_username = tk.Entry(frame, font=('Arial', 12), width=25)
        self.login_username.grid(row=0, column=1, padx=10)

        tk.Label(frame, text="Password:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=1, column=0, sticky='w', pady=5)
        self.login_password = tk.Entry(frame, font=('Arial', 12), width=25, show='*')
        self.login_password.grid(row=1, column=1, padx=10)

        tk.Button(frame, text="Login", font=('Arial', 12, 'bold'), bg='#3498db', fg='white',
                  command=self.login_user, width=20, pady=8).grid(row=2, column=0, columnspan=2, pady=15)

    def build_register(self, container):
        frame = tk.LabelFrame(container, text="Register New User", font=('Arial', 14, 'bold'),
                              fg='#e74c3c', bg='#2c3e50', padx=20, pady=20)
        frame.grid(row=0, column=1, padx=20, pady=10)

        tk.Label(frame, text="Username:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=0, column=0, sticky='w', pady=5)
        self.reg_username = tk.Entry(frame, font=('Arial', 12), width=25)
        self.reg_username.grid(row=0, column=1, padx=10)

        tk.Label(frame, text="Password:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=1, column=0, sticky='w', pady=5)
        self.reg_password = tk.Entry(frame, font=('Arial', 12), width=25, show='*')
        self.reg_password.grid(row=1, column=1, padx=10)

        tk.Label(frame, text="Confirm Password:", font=('Arial', 12), fg='#ecf0f1', bg='#2c3e50').grid(row=2, column=0, sticky='w', pady=5)
        self.reg_confirm_password = tk.Entry(frame, font=('Arial', 12), width=25, show='*')
        self.reg_confirm_password.grid(row=2, column=1, padx=10)

        tk.Button(frame, text="Register", font=('Arial', 12, 'bold'), bg='#e74c3c', fg='white',
                  command=self.register_user, width=20, pady=8).grid(row=3, column=0, columnspan=2, pady=15)

    def build_ml_features_info(self, container):
        """Build ML features information panel"""
        info_frame = tk.LabelFrame(container, text="🤖 AI Features", font=('Arial', 14, 'bold'),
                                  fg='#2ecc71', bg='#2c3e50', padx=20, pady=20)
        info_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky='ew')

        features_text = """✨ Enhanced with Machine Learning:
• Smart text detection at any angle
• High-accuracy medicine information extraction
• Auto-recognition of batch numbers and expiry dates
• Custom model training for better accuracy
• Multi-angle strip scanning capabilities"""

        tk.Label(info_frame, text=features_text, font=('Arial', 10),
                fg='#ecf0f1', bg='#2c3e50', justify=tk.LEFT).pack()

    def login_user(self):
        username, password = self.login_username.get().strip(), self.login_password.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        user_id = self.auth.login(username, password)
        if user_id:
            self.current_user_id, self.current_username = user_id, username
            self.create_enhanced_inventory_interface()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def register_user(self):
        u, p, cp = self.reg_username.get().strip(), self.reg_password.get().strip(), self.reg_confirm_password.get().strip()
        if not u or not p or not cp:
            messagebox.showerror("Error", "Please fill all fields")
            return
        if p != cp:
            messagebox.showerror("Error", "Passwords do not match")
            return
        if len(p) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return

        if self.auth.register(u, p):
            messagebox.showinfo("Success", "Registered! You can now login.")
            self.reg_username.delete(0, tk.END)
            self.reg_password.delete(0, tk.END)
            self.reg_confirm_password.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Username already exists")

    def create_enhanced_inventory_interface(self):
        """Create enhanced inventory interface with ML capabilities"""
        for widget in self.root.winfo_children():
            widget.destroy()

        # Main container
        self.main_container = tk.Frame(self.root, bg='#ecf0f1')
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Header with navigation
        self.create_header()

        # Create notebook for different views
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Inventory management tab
        self.create_inventory_tab()

        # AI Scanner tab
        if ML_AVAILABLE:
            self.create_ai_scanner_tab()
            self.create_training_tab()

        # Analytics tab
        self.create_analytics_tab()

    def create_header(self):
        """Create application header with navigation"""
        header_frame = tk.Frame(self.main_container, bg='#34495e', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Title and user info
        title_frame = tk.Frame(header_frame, bg='#34495e')
        title_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=10)

        tk.Label(title_frame, text="🏥 MediSort AI", font=('Arial', 15, 'bold'),
                fg='#ecf0f1', bg='#34495e').pack(anchor='w')
        tk.Label(title_frame, text=f"Welcome, {self.current_username}!",
                font=('Arial', 11), fg='#bdc3c7', bg='#34495e').pack(anchor='w')

        # Navigation buttons
        nav_frame = tk.Frame(header_frame, bg='#34495e')
        nav_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=15)

        # Logout button
        tk.Button(nav_frame, text="🚪 Logout", command=self.logout,
                 font=('Arial', 8, 'bold'), bg='#e74c3c', fg='white',
                 relief=tk.FLAT, padx=15).pack(side=tk.RIGHT, padx=5)

        # Settings button
        tk.Button(nav_frame, text="⚙️ Settings", command=self.show_settings,
                 font=('Arial', 8, 'bold'), bg='#95a5a6', fg='white',
                 relief=tk.FLAT, padx=15).pack(side=tk.RIGHT, padx=5)

    def create_inventory_tab(self):
        """Create inventory management tab"""
        inventory_frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(inventory_frame, text="📋 Inventory")

        # Split into form and list
        form_frame = tk.Frame(inventory_frame, bg='#ffffff', relief=tk.RAISED, bd=1)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        list_frame = tk.Frame(inventory_frame, bg='#ffffff', relief=tk.RAISED, bd=1)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)

        # Medicine form
        self.build_enhanced_inventory_form(form_frame)

        # Medicine list with enhanced features
        self.build_enhanced_medicine_list(list_frame)

        # Load initial data
        self.load_medicines()

    def create_ai_scanner_tab(self):
        """Create AI scanner tab"""
        scanner_frame = tk.Frame(self.notebook, bg='#f8f9fa')
        self.notebook.add(scanner_frame, text="🤖 AI Scanner")

        # Scanner interface
        scanner_title = tk.Label(scanner_frame, text="🤖 AI-Powered Medicine Scanner",
                                font=('Arial', 15, 'bold'), bg='#f8f9fa', fg='#2c3e50')
        scanner_title.pack(pady=20)

        # Scanner description
        desc_text = """The AI Scanner uses advanced machine learning to automatically detect and extract 
medicine information from strips at any angle. It can recognize:
• Medicine names and compositions
• Batch numbers and expiry dates
• Dosage and quantity information
• Manufacturer details"""

        desc_label = tk.Label(scanner_frame, text=desc_text, font=('Arial', 11),
                             bg='#f8f9fa', fg='#7f8c8d', justify=tk.LEFT)
        desc_label.pack(pady=10)

        # Scanner controls
        controls_frame = tk.Frame(scanner_frame, bg='#f8f9fa')
        controls_frame.pack(pady=30)

        tk.Button(controls_frame, text="📷 Start AI Scanner",
                 command=self.start_ai_scanner,
                 font=('Arial', 9, 'bold'), bg='#e74c3c', fg='white',
                 width=20, height=2, relief=tk.FLAT,
                 cursor='hand2').pack(pady=10)

        tk.Button(controls_frame, text="📁 Scan from File",
                 command=self.scan_from_file,
                 font=('Arial', 9, 'bold'), bg='#3498db', fg='white',
                 width=20, height=2, relief=tk.FLAT,
                 cursor='hand2').pack(pady=10)

    def create_training_tab(self):
        """Create ML model training tab"""
        training_frame = tk.Frame(self.notebook, bg='#f8f9fa')
        self.notebook.add(training_frame, text="🎓 AI Training")

        # Training interface
        training_title = tk.Label(training_frame, text="🎓 AI Model Training Center",
                                 font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#2c3e50')
        training_title.pack(pady=20)

        # Training description
        training_desc = """Train the AI model with your own medicine strip images to improve accuracy.
The more diverse training data you provide, the better the AI becomes at recognizing
different medicine formats and layouts."""

        tk.Label(training_frame, text=training_desc, font=('Arial', 11),
                bg='#f8f9fa', fg='#7f8c8d', justify=tk.CENTER,
                wraplength=600).pack(pady=10)

        # Training controls
        training_controls = tk.Frame(training_frame, bg='#f8f9fa')
        training_controls.pack(pady=30)

        tk.Button(training_controls, text="🎓 Start Training Interface",
                 command=self.start_training_interface,
                 font=('Arial', 10, 'bold'), bg='#9b59b6', fg='white',
                 width=25, height=2, relief=tk.FLAT,
                 cursor='hand2').pack(pady=10)

        # Model status
        self.create_model_status_panel(training_frame)

    def create_analytics_tab(self):
        """Create analytics and reporting tab"""
        analytics_frame = tk.Frame(self.notebook, bg='#ffffff')
        self.notebook.add(analytics_frame, text="📊 Analytics")

        # Analytics content
        tk.Label(analytics_frame, text="📊 Medicine Analytics Dashboard",
                font=('Arial', 13, 'bold'), bg='#ffffff', fg='#2c3e50').pack(pady=20)

        # Statistics panels
        stats_container = tk.Frame(analytics_frame, bg='#ffffff')
        stats_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.create_statistics_panels(stats_container)

    def build_enhanced_inventory_form(self, parent):
        """Build enhanced inventory form with AI integration"""
        form_title = tk.Label(parent, text="📝 Add/Edit Medicine",
                             font=('Arial', 10, 'bold'), bg='#ffffff', fg='#2c3e50')
        form_title.pack(pady=10)

        # Form fields
        fields = [
            ("Name:", 'name', 30),
            ("Quantity:", 'qty', 30),
            ("Expiry Date (YYYY-MM-DD):", 'expiry', 30),
            ("Batch Number:", 'batch', 30),
            ("Manufacturer:", 'manufacturer', 30)
        ]

        for label_text, field_name, width in fields:
            tk.Label(parent, text=label_text, font=('Arial', 8),
                    bg='#ffffff', fg='#2c3e50').pack(anchor='w', padx=20, pady=(10, 0))

            entry = tk.Entry(parent, font=('Arial', 8), width=width)
            entry.pack(padx=20, pady=(0, 5), fill=tk.X)
            setattr(self, f"med_{field_name}", entry)

        # Category dropdown
        tk.Label(parent, text="Category:", font=('Arial', 8),
                bg='#ffffff', fg='#2c3e50').pack(anchor='w', padx=20, pady=(10, 0))

        self.med_category = ttk.Combobox(parent, font=('Arial', 8), width=28,
                                        values=['Tablet', 'Capsule', 'Syrup', 'Injection',
                                               'Cream', 'Drops', 'Inhaler', 'Other'])
        self.med_category.pack(padx=20, pady=(0, 5), fill=tk.X)

        # Description
        tk.Label(parent, text="Description/Notes:", font=('Arial', 8),
                bg='#ffffff', fg='#2c3e50').pack(anchor='w', padx=20, pady=(10, 0))

        self.med_desc = tk.Text(parent, font=('Arial', 8), width=30, height=1)
        self.med_desc.pack(padx=20, pady=(0, 10), fill=tk.X)

        # Enhanced buttons
        button_frame = tk.Frame(parent, bg='#ffffff')
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # AI Scan button (prominent)
        if ML_AVAILABLE:
            tk.Button(button_frame, text="🤖 AI Scan",
                     command=self.enhanced_scan_webcam,
                     font=('Arial', 7, 'bold'), bg='#e74c3c', fg='white',
                     width=25, height=2, relief=tk.FLAT,
                     cursor='hand2').pack(pady=5, fill=tk.X)

        # Regular scan button
        tk.Button(button_frame, text="📷 Camera Scan",
                 command=self.scan_webcam,
                 font=('Arial', 7, 'bold'), bg='#3498db', fg='white',
                 width=25, relief=tk.FLAT,
                 cursor='hand2').pack(pady=2, fill=tk.X)

        # Add medicine button
        tk.Button(button_frame, text="➕ Add Medicine",
                 command=self.add_medicine,
                 font=('Arial', 7, 'bold'), bg='#27ae60', fg='white',
                 width=25, relief=tk.FLAT,
                 cursor='hand2').pack(pady=2, fill=tk.X)

        # Update button
        tk.Button(button_frame, text="📝 Update Selected",
                 command=self.update_medicine,
                 font=('Arial', 7, 'bold'), bg='#f39c12', fg='white',
                 width=25, relief=tk.FLAT,
                 cursor='hand2').pack(pady=2, fill=tk.X)

        # Delete button
        tk.Button(button_frame, text="🗑️ Delete Selected",
                 command=self.delete_selected,
                 font=('Arial', 7, 'bold'), bg='#e74c3c', fg='white',
                 width=25, relief=tk.FLAT,
                 cursor='hand2').pack(pady=2, fill=tk.X)

        # Clear form button
        tk.Button(button_frame, text="🧹 Clear Form",
                 command=self.clear_form,
                 font=('Arial', 7, 'bold'), bg='#95a5a6', fg='white',
                 width=25, relief=tk.FLAT,
                 cursor='hand2').pack(pady=2, fill=tk.X)

    def build_enhanced_medicine_list(self, parent):
        """Build enhanced medicine list with search and filters"""
        # List title and controls
        list_header = tk.Frame(parent, bg='#ffffff')
        list_header.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(list_header, text="📋 Medicine Inventory",
                font=('Arial', 12, 'bold'), bg='#ffffff', fg='#2c3e50').pack(side=tk.LEFT)

        # Search and filter controls
        controls_frame = tk.Frame(list_header, bg='#ffffff')
        controls_frame.pack(side=tk.RIGHT)

        # Search
        tk.Label(controls_frame, text="🔍 Search:", font=('Arial', 10),
                bg='#ffffff', fg='#2c3e50').pack(side=tk.LEFT, padx=(0, 5))

        self.search_entry = tk.Entry(controls_frame, font=('Arial', 10), width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)

        # Filter by expiry
        tk.Button(controls_frame, text="⚠️ Expiring Soon",
                 command=self.filter_expiring,
                 font=('Arial', 9, 'bold'), bg='#e67e22', fg='white',
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=2)

        # Refresh button
        tk.Button(controls_frame, text="🔄 Refresh",
                 command=self.load_medicines,
                 font=('Arial', 9, 'bold'), bg='#3498db', fg='white',
                 relief=tk.FLAT, cursor='hand2').pack(side=tk.LEFT, padx=2)

        # Treeview with scrollbar
        tree_container = tk.Frame(parent, bg='#ffffff')
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ('ID', 'Name', 'Qty', 'Expiry', 'Batch', 'Category', 'Manufacturer', 'Status')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=15)

        # Configure columns
        column_configs = {
            'ID': (50, 'center'),
            'Name': (150, 'w'),
            'Qty': (60, 'center'),
            'Expiry': (100, 'center'),
            'Batch': (100, 'center'),
            'Category': (80, 'center'),
            'Manufacturer': (120, 'w'),
            'Status': (80, 'center')
        }

        for col, (width, anchor) in column_configs.items():
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient='horizontal', command=self.tree.xview)

        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Configure row colors for status
        self.tree.tag_configure('expired', background='#ffcccc', foreground='#c0392b')
        self.tree.tag_configure('expiring', background='#ffe6cc', foreground='#e67e22')
        self.tree.tag_configure('low_stock', background='#fff2cc', foreground='#f39c12')
        self.tree.tag_configure('normal', background='#f8fff8', foreground='#27ae60')

        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def create_model_status_panel(self, parent):
        """Create model status and information panel"""
        status_frame = tk.LabelFrame(parent, text="🤖 AI Model Status",
                                    font=('Arial', 12, 'bold'),
                                    bg='#f8f9fa', fg='#2c3e50')
        status_frame.pack(fill=tk.X, padx=50, pady=20)

        # Model information
        if ML_AVAILABLE:
            available_models = self.ml_manager.get_available_models()
            model_count = len(available_models)

            status_text = f"📊 Available Models: {model_count}\n"
            if model_count > 0:
                status_text += f"🎯 Active Model: {available_models[0] if available_models else 'None'}\n"
                status_text += "✅ AI Features: Enabled"
            else:
                status_text += "⚠️ No trained models found\n"
                status_text += "💡 Train a model to enable AI features"
        else:
            status_text = "❌ ML components not available\n💡 Install required dependencies to enable AI features"

        tk.Label(status_frame, text=status_text, font=('Arial', 10),
                bg='#f8f9fa', fg='#2c3e50', justify=tk.LEFT).pack(pady=10)

    def create_statistics_panels(self, parent):
        """Create statistics panels for analytics"""
        # Create statistics grid
        stats_grid = tk.Frame(parent, bg='#ffffff')
        stats_grid.pack(fill=tk.BOTH, expand=True)

        # Get statistics from database
        stats = self.get_inventory_statistics()

        # Statistics cards
        stat_cards = [
            ("📦 Total Medicines", stats.get('total_medicines', 0), '#3498db'),
            ("⚠️ Expiring Soon", stats.get('expiring_soon', 0), '#e67e22'),
            ("❌ Expired", stats.get('expired', 0), '#e74c3c'),
            ("📉 Low Stock", stats.get('low_stock', 0), '#f39c12'),
            ("✅ Good Stock", stats.get('good_stock', 0), '#27ae60'),
            ("🏭 Unique Manufacturers", stats.get('unique_manufacturers', 0), '#9b59b6')
        ]

        # Create cards in grid
        for i, (title, value, color) in enumerate(stat_cards):
            row = i // 3
            col = i % 3

            card = tk.Frame(stats_grid, bg=color, relief=tk.RAISED, bd=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='ew')

            tk.Label(card, text=str(value), font=('Arial', 24, 'bold'),
                    bg=color, fg='white').pack(pady=(10, 0))
            tk.Label(card, text=title, font=('Arial', 10, 'bold'),
                    bg=color, fg='white').pack(pady=(0, 10))

        # Configure grid weights
        for i in range(3):
            stats_grid.columnconfigure(i, weight=1)

    # Enhanced methods with ML integration
    def enhanced_scan_webcam(self):
        """Enhanced webcam scanning with ML capabilities"""
        if not ML_AVAILABLE:
            messagebox.showwarning("ML Not Available", "ML components are not installed. Using basic scanning.")
            self.scan_webcam()
            return

        def on_ml_scan_complete(medicine_info):
            """Callback when ML scanning is complete"""
            if medicine_info:
                # Clear existing form data
                self.clear_form()

                # Populate form fields with ML results
                self.med_name.insert(0, medicine_info.get('name', ''))
                self.med_qty.insert(0, medicine_info.get('quantity', ''))
                self.med_batch.insert(0, medicine_info.get('batch_number', ''))
                self.med_manufacturer.insert(0, medicine_info.get('manufacturer', ''))

                # Handle expiry date format
                expiry = medicine_info.get('expiry_date', '')
                if expiry:
                    try:
                        if '/' in expiry:
                            parts = expiry.split('/')
                            if len(parts) == 3:
                                if len(parts[2]) == 2:  # YY format
                                    parts[2] = '20' + parts[2]
                                expiry = f"{parts[2]}-{parts[1]:0>2}-{parts[0]:0>2}"
                        elif '-' in expiry and len(expiry.split('-')[0]) == 2:
                            # Convert DD-MM-YYYY to YYYY-MM-DD
                            parts = expiry.split('-')
                            if len(parts) == 3:
                                expiry = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    except:
                        pass
                self.med_expiry.insert(0, expiry)

                # Set category based on detected information
                name_lower = medicine_info.get('name', '').lower()
                if any(word in name_lower for word in ['tablet', 'tab']):
                    self.med_category.set('Tablet')
                elif any(word in name_lower for word in ['capsule', 'cap']):
                    self.med_category.set('Capsule')
                elif 'syrup' in name_lower:
                    self.med_category.set('Syrup')
                elif 'injection' in name_lower:
                    self.med_category.set('Injection')
                elif 'cream' in name_lower:
                    self.med_category.set('Cream')
                else:
                    self.med_category.set('Other')

                # Add description with ML extraction info
                confidence = medicine_info.get('confidence', 0)
                desc_text = f"🤖 AI Extracted Information:\n"
                desc_text += f"Confidence Score: {confidence:.1%}\n"
                desc_text += f"Strength: {medicine_info.get('strength', 'N/A')}\n"
                desc_text += f"Composition: {medicine_info.get('composition', 'N/A')}\n"

                self.med_desc.delete(1.0, tk.END)
                self.med_desc.insert(1.0, desc_text)

                # Show success message
                messagebox.showinfo("AI Scan Complete",
                                  f"Medicine information extracted with {confidence:.1%} confidence.\n"
                                  "Please verify the information before adding to inventory.")

        # Start ML scanner
        try:
            ml_scanner = MLMedicineScanner(self.root, callback=on_ml_scan_complete)
            ml_scanner.start_scanning()
        except Exception as e:
            messagebox.showerror("Scanner Error", f"Failed to start AI scanner: {e}")
            self.scan_webcam()  # Fallback to regular scan

    def scan_webcam(self):
        """Traditional webcam scanning method"""
        cap = cv2.VideoCapture(0)
        messagebox.showinfo("Instructions", "Press SPACE to capture, ESC to cancel.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Scan Medicine Label - Press SPACE to Capture", frame)
            k = cv2.waitKey(1)
            if k % 256 == 27:  # ESC
                break
            elif k % 256 == 32:  # SPACE
                text = pytesseract.image_to_string(frame)
                self.populate_fields_from_text(text)
                break

        cap.release()
        cv2.destroyAllWindows()

    def populate_fields_from_text(self, text):
        """Populate form fields from OCR text"""
        lines = text.splitlines()
        found_qty = found_exp = found_name = False

        date_pattern1 = re.compile(r'\d{4}-\d{2}-\d{2}')
        date_pattern2 = re.compile(r'\d{2}/\d{2}/\d{4}')
        qty_pattern = re.compile(r'(\d+)\s*(tabs|tablets|caps|capsules|ml|pcs|pieces|qty|quantity)?', re.I)

        for line in lines:
            l = line.lower().strip()

            if not found_qty:
                m = qty_pattern.search(l)
                if m:
                    qty = m.group(1)
                    self.med_qty.delete(0, tk.END)
                    self.med_qty.insert(0, qty)
                    found_qty = True

            if not found_exp:
                m1 = date_pattern1.search(l)
                m2 = date_pattern2.search(l)
                if m1:
                    self.med_expiry.delete(0, tk.END)
                    self.med_expiry.insert(0, m1.group(0))
                    found_exp = True
                elif m2:
                    d, m, y = m2.group(0).split('/')
                    self.med_expiry.delete(0, tk.END)
                    self.med_expiry.insert(0, f"{y}-{m:0>2}-{d:0>2}")
                    found_exp = True

            if not found_name and len(l) > 3 and not any(x in l for x in ["qty", "quantity", "exp", "expiry"]):
                self.med_name.delete(0, tk.END)
                self.med_name.insert(0, line.strip())
                found_name = True

        self.med_category.set("Tablet")

    def start_ai_scanner(self):
        """Start the AI scanner interface"""
        if not ML_AVAILABLE:
            messagebox.showwarning("ML Not Available", "ML components are not installed.")
            return

        try:
            ml_scanner = MLMedicineScanner(self.root, callback=self.on_ai_scan_result)
            ml_scanner.start_scanning()
        except Exception as e:
            messagebox.showerror("Scanner Error", f"Failed to start AI scanner: {e}")

    def scan_from_file(self):
        """Scan medicine information from image file"""
        from tkinter import filedialog

        filetypes = [
            ('Image files', '*.png *.jpg *.jpeg *.bmp *.tiff'),
            ('All files', '*.*')
        ]

        filename = filedialog.askopenfilename(
            title="Select medicine strip image",
            filetypes=filetypes
        )

        if filename:
            try:
                # Load and process image
                image = cv2.imread(filename)

                if ML_AVAILABLE:
                    # Use ML processing
                    ml_model = MLMedicineScanner(self.root)
                    # Process image with ML
                    messagebox.showinfo("Processing", "Processing image with AI...")
                else:
                    # Use traditional OCR
                    text = pytesseract.image_to_string(image)
                    self.populate_fields_from_text(text)
                    messagebox.showinfo("Scan Complete", "Image processed with traditional OCR.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to process image: {e}")

    def start_training_interface(self):
        """Start the ML training interface"""
        if not ML_AVAILABLE:
            messagebox.showwarning("ML Not Available", "ML components are not installed.")
            return

        try:
            if not self.ml_training_interface:
                self.ml_training_interface = MLTrainingInterface(self.root)
            self.ml_training_interface.start_training_interface()
        except Exception as e:
            messagebox.showerror("Training Error", f"Failed to start training interface: {e}")

    def on_ai_scan_result(self, medicine_info):
        """Handle AI scan result"""
        if medicine_info:
            # Switch to inventory tab
            self.notebook.select(0)

            # Populate form with scan results
            self.clear_form()
            self.med_name.insert(0, medicine_info.get('name', ''))
            self.med_qty.insert(0, medicine_info.get('quantity', ''))
            self.med_batch.insert(0, medicine_info.get('batch_number', ''))
            # ... populate other fields

    def load_medicines(self):
        """Load medicines from database with enhanced display"""
        # Clear existing items
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, quantity, expiry_date, batch_number, 
                           category, manufacturer, description 
                    FROM medicines 
                    WHERE user_id = ? 
                    ORDER BY expiry_date ASC
                ''', (self.current_user_id,))

                medicines = cursor.fetchall()

                for medicine in medicines:
                    med_id, name, qty, expiry, batch, category, manufacturer, desc = medicine

                    # Calculate status
                    status, tag = self.calculate_medicine_status(expiry, qty)

                    # Insert into tree
                    item = self.tree.insert('', tk.END, values=(
                        med_id, name, qty, expiry, batch or 'N/A',
                        category or 'N/A', manufacturer or 'N/A', status
                    ))

                    # Apply tag for coloring
                    if tag:
                        self.tree.item(item, tags=(tag,))

        except sqlite3.Error as e:
            messagebox.showerror("Database Error",
                                 f"Failed to load medicines: {e}\n\nPlease ensure the database schema is correct.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
    def calculate_medicine_status(self, expiry_date, quantity):
        """Calculate medicine status and return status text and tag"""
        from datetime import datetime, timedelta

        try:
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            today = datetime.now()
            days_left = (expiry - today).days

            if days_left < 0:
                return "EXPIRED", "expired"
            elif days_left <= 7:
                return "EXPIRING", "expiring"
            elif quantity < 5:
                return "LOW STOCK", "low_stock"
            else:
                return "GOOD", "normal"

        except:
            return "UNKNOWN", "normal"

    def on_search(self, event=None):
        """Handle search functionality"""
        search_term = self.search_entry.get().lower()

        if not search_term:
            self.load_medicines()
            return

        # Filter displayed items
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            # Search in name, batch, manufacturer
            if any(search_term in str(val).lower() for val in [values[1], values[4], values[6]]):
                self.tree.reattach(item, '', tk.END)
            else:
                self.tree.detach(item)

    def filter_expiring(self):
        """Filter to show only expiring medicines"""
        from datetime import datetime, timedelta

        # Clear and reload with filter
        for row in self.tree.get_children():
            self.tree.delete(row)

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, quantity, expiry_date, batch_number, 
                           category, manufacturer, description 
                    FROM medicines 
                    WHERE user_id = ? AND expiry_date <= date('now', '+30 days')
                    ORDER BY expiry_date ASC
                ''', (self.current_user_id,))

                medicines = cursor.fetchall()

                for medicine in medicines:
                    med_id, name, qty, expiry, batch, category, manufacturer, desc = medicine
                    status, tag = self.calculate_medicine_status(expiry, qty)

                    item = self.tree.insert('', tk.END, values=(
                        med_id, name, qty, expiry, batch or 'N/A',
                        category or 'N/A', manufacturer or 'N/A', status
                    ))

                    if tag:
                        self.tree.item(item, tags=(tag,))

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to filter medicines: {e}")

    def on_tree_select(self, event):
        """Handle tree selection to populate form for editing"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item)['values']

            # Clear and populate form
            self.clear_form()

            # Get full medicine data
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT name, quantity, expiry_date, batch_number, 
                               category, manufacturer, description 
                        FROM medicines WHERE id = ?
                    ''', (values[0],))

                    medicine = cursor.fetchone()
                    if medicine:
                        name, qty, expiry, batch, category, manufacturer, desc = medicine

                        self.med_name.insert(0, name)
                        self.med_qty.insert(0, str(qty))
                        self.med_expiry.insert(0, expiry)
                        self.med_batch.insert(0, batch or '')
                        self.med_category.set(category or 'Other')
                        self.med_manufacturer.insert(0, manufacturer or '')
                        self.med_desc.insert(1.0, desc or '')

            except Exception as e:
                print(f"Error loading medicine details: {e}")

    def add_medicine(self):
        """Add medicine to inventory"""
        name = self.med_name.get().strip()
        qty = self.med_qty.get().strip()
        expiry = self.med_expiry.get().strip()
        batch = self.med_batch.get().strip()
        category = self.med_category.get()
        manufacturer = self.med_manufacturer.get().strip()
        description = self.med_desc.get("1.0", tk.END).strip()

        # Validation
        if not all([name, qty, expiry, category]):
            messagebox.showerror("Error", "Please fill all required fields (Name, Quantity, Expiry Date, Category)")
            return

        try:
            qty = int(qty)
            datetime.strptime(expiry, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity or date format")
            return

        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    INSERT INTO medicines 
                    (user_id, name, quantity, expiry_date, batch_number, category, manufacturer, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.current_user_id, name, qty, expiry, batch, category, manufacturer, description))

            messagebox.showinfo("Success", "Medicine added successfully!")
            self.clear_form()
            self.load_medicines()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add medicine: {e}")

    def update_medicine(self):
        """Update selected medicine"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a medicine to update")
            return

        med_id = self.tree.item(selection[0])['values'][0]

        # Get form data
        name = self.med_name.get().strip()
        qty = self.med_qty.get().strip()
        expiry = self.med_expiry.get().strip()
        batch = self.med_batch.get().strip()
        category = self.med_category.get()
        manufacturer = self.med_manufacturer.get().strip()
        description = self.med_desc.get("1.0", tk.END).strip()

        # Validation
        if not all([name, qty, expiry, category]):
            messagebox.showerror("Error", "Please fill all required fields")
            return

        try:
            qty = int(qty)
            datetime.strptime(expiry, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity or date format")
            return

        try:
            with self.db_manager.get_connection() as conn:
                conn.execute('''
                    UPDATE medicines 
                    SET name=?, quantity=?, expiry_date=?, batch_number=?, 
                        category=?, manufacturer=?, description=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=? AND user_id=?
                ''', (name, qty, expiry, batch, category, manufacturer, description, med_id, self.current_user_id))

            messagebox.showinfo("Success", "Medicine updated successfully!")
            self.clear_form()
            self.load_medicines()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update medicine: {e}")

    def delete_selected(self):
        """Delete selected medicine"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a medicine to delete")
            return

        med_id = self.tree.item(selection[0])['values'][0]
        med_name = self.tree.item(selection[0])['values'][1]

        # Confirm deletion
        result = messagebox.askyesno("Confirm Deletion",
                                   f"Are you sure you want to delete '{med_name}'?")

        if result:
            try:
                with self.db_manager.get_connection() as conn:
                    conn.execute("DELETE FROM medicines WHERE id=? AND user_id=?",
                               (med_id, self.current_user_id))

                messagebox.showinfo("Success", "Medicine deleted successfully!")
                self.load_medicines()
                self.clear_form()

            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete medicine: {e}")

    def clear_form(self):
        """Clear all form fields"""
        self.med_name.delete(0, tk.END)
        self.med_qty.delete(0, tk.END)
        self.med_expiry.delete(0, tk.END)
        self.med_batch.delete(0, tk.END)
        self.med_category.set('')
        self.med_manufacturer.delete(0, tk.END)
        self.med_desc.delete(1.0, tk.END)

    def get_inventory_statistics(self):
        """Get inventory statistics for analytics"""
        from datetime import datetime, timedelta

        stats = {}

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Total medicines
                cursor.execute("SELECT COUNT(*) FROM medicines WHERE user_id = ?", (self.current_user_id,))
                stats['total_medicines'] = cursor.fetchone()[0]

                # Expiring soon (next 30 days)
                cursor.execute('''
                    SELECT COUNT(*) FROM medicines 
                    WHERE user_id = ? AND expiry_date <= date('now', '+30 days') AND expiry_date >= date('now')
                ''', (self.current_user_id,))
                stats['expiring_soon'] = cursor.fetchone()[0]

                # Expired
                cursor.execute('''
                    SELECT COUNT(*) FROM medicines 
                    WHERE user_id = ? AND expiry_date < date('now')
                ''', (self.current_user_id,))
                stats['expired'] = cursor.fetchone()[0]

                # Low stock (quantity < 5)
                cursor.execute('''
                    SELECT COUNT(*) FROM medicines 
                    WHERE user_id = ? AND quantity < 5
                ''', (self.current_user_id,))
                stats['low_stock'] = cursor.fetchone()[0]

                # Good stock
                cursor.execute('''
                    SELECT COUNT(*) FROM medicines 
                    WHERE user_id = ? AND quantity >= 5 AND expiry_date > date('now', '+30 days')
                ''', (self.current_user_id,))
                stats['good_stock'] = cursor.fetchone()[0]

                # Unique manufacturers
                cursor.execute('''
                    SELECT COUNT(DISTINCT manufacturer) FROM medicines 
                    WHERE user_id = ? AND manufacturer IS NOT NULL AND manufacturer != ''
                ''', (self.current_user_id,))
                stats['unique_manufacturers'] = cursor.fetchone()[0]

        except Exception as e:
            print(f"Error getting statistics: {e}")
            # Return default stats
            stats = {
                'total_medicines': 0,
                'expiring_soon': 0,
                'expired': 0,
                'low_stock': 0,
                'good_stock': 0,
                'unique_manufacturers': 0
            }

        return stats

    def show_settings(self):
        """Show application settings"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg='#f8f9fa')

        tk.Label(settings_window, text="⚙️ Application Settings",
                font=('Arial', 16, 'bold'), bg='#f8f9fa', fg='#2c3e50').pack(pady=20)

        # Settings options
        settings_frame = tk.LabelFrame(settings_window, text="General Settings",
                                     font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#2c3e50')
        settings_frame.pack(fill=tk.X, padx=20, pady=10)

        # Database backup
        tk.Button(settings_frame, text="📦 Backup Database",
                 command=self.backup_database,
                 font=('Arial', 10, 'bold'), bg='#3498db', fg='white',
                 width=20, relief=tk.FLAT).pack(pady=10)

        # Export data
        tk.Button(settings_frame, text="📤 Export Data",
                 command=self.export_data,
                 font=('Arial', 10, 'bold'), bg='#27ae60', fg='white',
                 width=20, relief=tk.FLAT).pack(pady=5)

        # Import data
        tk.Button(settings_frame, text="📥 Import Data",
                 command=self.import_data,
                 font=('Arial', 10, 'bold'), bg='#f39c12', fg='white',
                 width=20, relief=tk.FLAT).pack(pady=5)

    def backup_database(self):
        """Backup database"""
        from tkinter import filedialog
        import shutil

        filename = filedialog.asksaveasfilename(
            defaultextension='.db',
            filetypes=[('Database files', '*.db'), ('All files', '*.*')],
            title="Save database backup"
        )

        if filename:
            try:
                shutil.copy2(self.db_manager.db_path, filename)
                messagebox.showinfo("Success", f"Database backed up to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to backup database: {e}")

    def export_data(self):
        """Export medicine data to CSV"""
        from tkinter import filedialog
        import csv

        filename = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
            title="Export medicine data"
        )

        if filename:
            try:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT name, quantity, expiry_date, batch_number, 
                               category, manufacturer, description, created_at
                        FROM medicines WHERE user_id = ?
                    ''', (self.current_user_id,))

                    medicines = cursor.fetchall()

                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Name', 'Quantity', 'Expiry Date', 'Batch Number',
                                   'Category', 'Manufacturer', 'Description', 'Created At'])
                    writer.writerows(medicines)

                messagebox.showinfo("Success", f"Data exported to {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")

    def import_data(self):
        """Import medicine data from CSV"""
        from tkinter import filedialog
        import csv

        filename = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
            title="Import medicine data"
        )

        if filename:
            try:
                imported_count = 0

                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)

                    with self.db_manager.get_connection() as conn:
                        for row in reader:
                            try:
                                conn.execute('''
                                    INSERT INTO medicines 
                                    (user_id, name, quantity, expiry_date, batch_number, 
                                     category, manufacturer, description)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    self.current_user_id,
                                    row.get('Name', ''),
                                    int(row.get('Quantity', 0)),
                                    row.get('Expiry Date', ''),
                                    row.get('Batch Number', ''),
                                    row.get('Category', 'Other'),
                                    row.get('Manufacturer', ''),
                                    row.get('Description', '')
                                ))
                                imported_count += 1

                            except Exception as e:
                                print(f"Error importing row: {e}")
                                continue

                self.load_medicines()
                messagebox.showinfo("Success", f"Imported {imported_count} medicines successfully!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to import data: {e}")

    def logout(self):
        """Logout and return to main interface"""
        self.current_user_id = None
        self.current_username = None
        self.create_main_interface()

    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    # Create and run the enhanced application
    app = EnhancedMediSortApp()
    app.run()



//
