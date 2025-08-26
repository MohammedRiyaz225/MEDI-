import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import heapq
from collections import defaultdict


class MedicineNode:
    """Node class for medicine data with comparison methods"""

    def __init__(self, medicine_data):
        self.id = medicine_data[0]
        self.name = medicine_data[1]
        self.expiry_date = medicine_data[2]
        self.batch_number = medicine_data[3]
        self.quantity = medicine_data[4]
        self.notes = medicine_data[5]
        self.created_at = medicine_data[6]

    def __lt__(self, other):
        """Less than comparison for heap operations (based on expiry date)"""
        return self.expiry_date < other.expiry_date

    def __eq__(self, other):
        """Equality comparison"""
        return self.id == other.id

    def days_until_expiry(self):
        """Calculate days until expiry"""
        try:
            expiry = datetime.strptime(self.expiry_date, '%Y-%m-%d')
            today = datetime.now()
            return (expiry - today).days
        except:
            return 999  # Default to far future if date parsing fails


class InventoryManager:
    def __init__(self, db_handler, current_user):
        self.db_handler = db_handler
        self.current_user = current_user
        self.medicines_data = []
        self.filtered_data = []
        self.sort_column = 'expiry_date'
        self.sort_reverse = False

    def create_inventory_interface(self, parent):
        """Create the inventory management interface"""
        # Main container
        main_frame = tk.Frame(parent, bg='white')
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        # Title
        title_label = tk.Label(main_frame, text="Medicine Inventory",
                               font=('Arial', 16, 'bold'),
                               bg='white', fg='#2c3e50')
        title_label.pack(pady=(0, 20))

        # Top controls frame
        controls_frame = tk.Frame(main_frame, bg='white')
        controls_frame.pack(fill='x', pady=(0, 10))

        # Search frame
        search_frame = tk.Frame(controls_frame, bg='white')
        search_frame.pack(side='left', fill='x', expand=True)

        tk.Label(search_frame, text="Search:", bg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 5))

        self.search_entry = tk.Entry(search_frame, font=('Arial', 10), width=30)
        self.search_entry.pack(side='left', padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)

        # Search button
        search_btn = tk.Button(search_frame, text="Search",
                               command=self.search_medicines,
                               bg='#3498db', fg='white',
                               font=('Arial', 9, 'bold'))
        search_btn.pack(side='left', padx=5)

        # Clear search button
        clear_btn = tk.Button(search_frame, text="Clear",
                              command=self.clear_search,
                              bg='#95a5a6', fg='white',
                              font=('Arial', 9, 'bold'))
        clear_btn.pack(side='left', padx=5)

        # Action buttons frame
        actions_frame = tk.Frame(controls_frame, bg='white')
        actions_frame.pack(side='right')

        # Add medicine button
        add_btn = tk.Button(actions_frame, text="Add Medicine",
                            command=self.show_add_medicine_dialog,
                            bg='#2ecc71', fg='white',
                            font=('Arial', 10, 'bold'),
                            padx=15, pady=5)
        add_btn.pack(side='left', padx=5)

        # Edit medicine button
        edit_btn = tk.Button(actions_frame, text="Edit Selected",
                             command=self.edit_selected_medicine,
                             bg='#f39c12', fg='white',
                             font=('Arial', 10, 'bold'),
                             padx=15, pady=5)
        edit_btn.pack(side='left', padx=5)

        # Delete medicine button
        delete_btn = tk.Button(actions_frame, text="Delete Selected",
                               command=self.delete_selected_medicine,
                               bg='#e74c3c', fg='white',
                               font=('Arial', 10, 'bold'),
                               padx=15, pady=5)
        delete_btn.pack(side='left', padx=5)

        # Refresh button
        refresh_btn = tk.Button(actions_frame, text="Refresh",
                                command=self.refresh_inventory,
                                bg='#9b59b6', fg='white',
                                font=('Arial', 10, 'bold'),
                                padx=15, pady=5)
        refresh_btn.pack(side='left', padx=5)

        # Sorting controls
        sort_frame = tk.Frame(main_frame, bg='white')
        sort_frame.pack(fill='x', pady=(0, 10))

        tk.Label(sort_frame, text="Sort by:", bg='white',
                 font=('Arial', 10, 'bold')).pack(side='left', padx=(0, 5))

        self.sort_var = tk.StringVar(value='expiry_date')
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var,
                                  values=['name', 'expiry_date', 'quantity', 'created_at'],
                                  state='readonly', width=15)
        sort_combo.pack(side='left', padx=5)
        sort_combo.bind('<<ComboboxSelected>>', self.on_sort_change)

        # Sort order
        self.sort_order_var = tk.StringVar(value='Ascending')
        order_combo = ttk.Combobox(sort_frame, textvariable=self.sort_order_var,
                                   values=['Ascending', 'Descending'],
                                   state='readonly', width=12)
        order_combo.pack(side='left', padx=5)
        order_combo.bind('<<ComboboxSelected>>', self.on_sort_change)

        # Priority alerts frame
        alerts_frame = tk.Frame(sort_frame, bg='white')
        alerts_frame.pack(side='right')

        # Show expiring medicines
        expiring_btn = tk.Button(alerts_frame, text="Show Expiring Soon",
                                 command=self.show_expiring_medicines,
                                 bg='#e67e22', fg='white',
                                 font=('Arial', 9, 'bold'))
        expiring_btn.pack(side='left', padx=5)

        # Show low stock
        low_stock_btn = tk.Button(alerts_frame, text="Show Low Stock",
                                  command=self.show_low_stock_medicines,
                                  bg='#c0392b', fg='white',
                                  font=('Arial', 9, 'bold'))
        low_stock_btn.pack(side='left', padx=5)

        # Table frame
        table_frame = tk.Frame(main_frame, bg='white')
        table_frame.pack(expand=True, fill='both')

        # Create treeview
        columns = ('ID', 'Name', 'Expiry Date', 'Batch Number', 'Quantity', 'Days Left', 'Status')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('Name', text='Medicine Name')
        self.tree.heading('Expiry Date', text='Expiry Date')
        self.tree.heading('Batch Number', text='Batch Number')
        self.tree.heading('Quantity', text='Quantity')
        self.tree.heading('Days Left', text='Days Left')
        self.tree.heading('Status', text='Status')

        # Configure column widths
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Name', width=200, anchor='w')
        self.tree.column('Expiry Date', width=120, anchor='center')
        self.tree.column('Batch Number', width=120, anchor='center')
        self.tree.column('Quantity', width=80, anchor='center')
        self.tree.column('Days Left', width=80, anchor='center')
        self.tree.column('Status', width=100, anchor='center')

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)

        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack scrollbars and treeview
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        self.tree.pack(expand=True, fill='both')

        # Configure row colors
        self.tree.tag_configure('expired', background='#ffcccc')
        self.tree.tag_configure('expiring', background='#ffe6cc')
        self.tree.tag_configure('low_stock', background='#fff2cc')
        self.tree.tag_configure('critical', background='#ff9999')

        # Load initial data
        self.refresh_inventory()

    def refresh_inventory(self):
        """Refresh inventory data from database"""
        try:
            from auth import AuthManager
            auth_manager = AuthManager(self.db_handler)
            user_id = auth_manager.get_user_id(self.current_user)

            conn = self.db_handler.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, name, expiry_date, batch_number, quantity, notes, created_at
                FROM medicines
                WHERE user_id = ?
                ORDER BY expiry_date ASC
            ''', (user_id,))

            self.medicines_data = cursor.fetchall()
            conn.close()

            # Apply current sorting
            self.sort_medicines()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh inventory: {e}")

    def sort_medicines(self):
        """Sort medicines using DSA concepts"""
        if not self.medicines_data:
            self.filtered_data = []
            self.update_tree_display()
            return

        # Create medicine nodes
        medicine_nodes = [MedicineNode(med) for med in self.medicines_data]

        # Sort based on selected column
        if self.sort_column == 'expiry_date':
            # Use heap sort for expiry dates (priority queue concept)
            self.filtered_data = self.heap_sort_by_expiry(medicine_nodes)
        elif self.sort_column == 'name':
            # Use merge sort for names
            self.filtered_data = self.merge_sort_by_name(medicine_nodes)
        elif self.sort_column == 'quantity':
            # Use quick sort for quantities
            self.filtered_data = self.quick_sort_by_quantity(medicine_nodes)
        else:
            # Default sorting
            medicine_nodes.sort(key=lambda x: getattr(x, self.sort_column), reverse=self.sort_reverse)
            self.filtered_data = medicine_nodes

        self.update_tree_display()

    def heap_sort_by_expiry(self, medicine_nodes):
        """Sort medicines by expiry date using heap sort"""
        if not medicine_nodes:
            return []

        # Create min heap
        heap = []
        for node in medicine_nodes:
            heapq.heappush(heap, (node.expiry_date, node))

        # Extract sorted elements
        sorted_medicines = []
        while heap:
            _, node = heapq.heappop(heap)
            sorted_medicines.append(node)

        if self.sort_reverse:
            sorted_medicines.reverse()

        return sorted_medicines

    def merge_sort_by_name(self, medicine_nodes):
        """Sort medicines by name using merge sort"""
        if len(medicine_nodes) <= 1:
            return medicine_nodes

        mid = len(medicine_nodes) // 2
        left = self.merge_sort_by_name(medicine_nodes[:mid])
        right = self.merge_sort_by_name(medicine_nodes[mid:])

        return self.merge_by_name(left, right)

    def merge_by_name(self, left, right):
        """Merge two sorted lists by name"""
        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            if (left[i].name.lower() <= right[j].name.lower()) != self.sort_reverse:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

        result.extend(left[i:])
        result.extend(right[j:])

        return result

    def quick_sort_by_quantity(self, medicine_nodes):
        """Sort medicines by quantity using quick sort"""
        if len(medicine_nodes) <= 1:
            return medicine_nodes

        pivot = medicine_nodes[len(medicine_nodes) // 2]
        left = [x for x in medicine_nodes if (x.quantity < pivot.quantity) != self.sort_reverse]
        middle = [x for x in medicine_nodes if x.quantity == pivot.quantity]
        right = [x for x in medicine_nodes if (x.quantity > pivot.quantity) != self.sort_reverse]

        return self.quick_sort_by_quantity(left) + middle + self.quick_sort_by_quantity(right)

    def update_tree_display(self):
        """Update the tree display with current data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add medicines to tree
        for medicine in self.filtered_data:
            days_left = medicine.days_until_expiry()

            # Determine status and tag
            if days_left < 0:
                status = "EXPIRED"
                tag = "expired"
            elif days_left <= 7:
                status = "EXPIRING"
                tag = "expiring"
            elif medicine.quantity < 5:
                status = "LOW STOCK"
                tag = "low_stock"
            else:
                status = "GOOD"
                tag = ""

            # Critical items (expired + low stock)
            if days_left < 0 and medicine.quantity < 5:
                tag = "critical"

            item = self.tree.insert('', 'end', values=(
                medicine.id,
                medicine.name,
                medicine.expiry_date,
                medicine.batch_number or 'N/A',
                medicine.quantity,
                days_left if days_left >= 0 else 'EXPIRED',
                status
            ))

            if tag:
                self.tree.set(item, 'Status', status)
                self.tree.item(item, tags=(tag,))

    def on_search(self, event=None):
        """Handle search as user types"""
        search_term = self.search_entry.get().lower()
        if not search_term:
            self.filtered_data = [MedicineNode(med) for med in self.medicines_data]
        else:
            self.filtered_data = [
                MedicineNode(med) for med in self.medicines_data
                if search_term in med[1].lower() or  # name
                   search_term in (med[3] or '').lower()  # batch number
            ]
        self.update_tree_display()

    def search_medicines(self):
        """Search medicines using binary search on sorted data"""
        search_term = self.search_entry.get().strip().lower()
        if not search_term:
            self.clear_search()
            return

        # Filter medicines
        filtered_medicines = []
        for med in self.medicines_data:
            if (search_term in med[1].lower() or  # name
                    search_term in (med[3] or '').lower() or  # batch number
                    search_term in (med[5] or '').lower()):  # notes
                filtered_medicines.append(med)

        self.filtered_data = [MedicineNode(med) for med in filtered_medicines]
        self.update_tree_display()

    def clear_search(self):
        """Clear search and show all medicines"""
        self.search_entry.delete(0, tk.END)
        self.sort_medicines()

    def on_sort_change(self, event=None):
        """Handle sort column or order change"""
        self.sort_column = self.sort_var.get()
        self.sort_reverse = (self.sort_order_var.get() == 'Descending')
        self.sort_medicines()

    def get_expiring_medicines(self):
        """Get medicines expiring within 7 days using priority queue"""
        expiring = []
        for med in self.medicines_data:
            medicine_node = MedicineNode(med)
            if 0 <= medicine_node.days_until_expiry() <= 7:
                expiring.append(medicine_node)
        return expiring

    def get_low_stock_medicines(self):
        """Get medicines with low stock (< 5 units)"""
        low_stock = []
        for med in self.medicines_data:
            if med[4] < 5:  # quantity
                low_stock.append(MedicineNode(med))
        return low_stock

    def show_expiring_medicines(self):
        """Show only medicines expiring soon"""
        expiring = self.get_expiring_medicines()
        self.filtered_data = sorted(expiring, key=lambda x: x.days_until_expiry())
        self.update_