import flet as ft
from config.database import get_db_connection, get_employee_full_name
from views.order_window import fetch_transaction_and_orders, page as order_page
import os
import glob

def get_admin_full_name():
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT full_name FROM admin LIMIT 1")
            admin = cursor.fetchone()
            cursor.close()
            conn.close()
            return admin[0] if admin else "Admin"
    except Exception as e:
        print(f"Error fetching admin name: {e}")
        return "Admin"

admin_full_name = get_admin_full_name()

def delete_transaction_and_orders(transaction_id, page, refresh_callback):
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()
            # Delete orders first
            cursor.execute("DELETE FROM orders WHERE transaction_id = %s", (transaction_id,))
            # Delete transaction
            cursor.execute("DELETE FROM transactions WHERE transaction_id = %s", (transaction_id,))
            conn.commit()
            cursor.close()
            conn.close()
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Transaction deleted successfully!"),
            bgcolor="#4CAF50"
        )
        page.snack_bar.open = True
        page.update()
        refresh_callback()
    except Exception as e:
        print(f"Error deleting transaction: {e}")
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Error deleting transaction!"),
            bgcolor="#F44336"
        )
        page.snack_bar.open = True
        page.update()

def transactions_view(page: ft.Page):
    # Fetch logged-in user's name
    def get_logged_in_user():
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("SELECT first_name, last_name FROM employees WHERE id = %s", (page.session.get("user_id"),))
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                return f"{user[0]} {user[1]}" if user else "User"
        except Exception as e:
            print(f"Error fetching user: {e}")
            return "User"

    user_name = get_logged_in_user()

    # Header Section
    header = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Transactions", size=24, weight="bold", color="#BB6F19"),
                    ft.Text("Monday, 25 March 2025", size=14, color="black"),  # Example date
                ],
                expand=True
            ),
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.CircleAvatar(
                            content=ft.Icon(ft.Icons.PERSON, color="black"),
                            bgcolor="#BB6F19",
                            radius=18
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(user_name, weight="bold", size=16, font_family="Poppins"),
                            ],
                            spacing=0
                        ),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            icon_color="black",
                            tooltip="Logout",
                            on_click=lambda e: handle_logout(page)
                        )
                    ],
                    spacing=10,
                    alignment="center"
                ),
                padding=10,
                border_radius=25,
                bgcolor="white",
                shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.1, "black")),
            )
        ],
        alignment="spaceBetween",
        vertical_alignment="center"
    )

    def handle_logout(page):
        # Create a custom modal dialog for logout confirmation (standardized)
        logout_modal = ft.Container(
            visible=False,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            expand=True,
            content=ft.Container(
                width=400,
                height=150,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                padding=ft.padding.all(20),
                alignment=ft.alignment.center,
                content=ft.Column(
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Confirm Logout", size=18, weight="bold"),
                        ft.Text("Are you sure you want to logout?", size=14, color=ft.Colors.GREY),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10,
                            controls=[
                                ft.ElevatedButton(
                                    "Cancel",
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.GREY,
                                        color=ft.Colors.WHITE,
                                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    on_click=lambda e: close_logout_modal(),
                                ),
                                ft.ElevatedButton(
                                    "Logout",
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.RED,
                                        color=ft.Colors.WHITE,
                                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    on_click=lambda e: confirm_logout(),
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        )
        page.overlay.append(logout_modal)
        def confirm_logout():
            logout_modal.visible = False
            page.overlay.remove(logout_modal)
            page.update()
            page.clean()
            page.bgcolor = "white"
            from views.login import main
            main(page)
            page.update()
        def close_logout_modal():
            logout_modal.visible = False
            page.overlay.remove(logout_modal)
            page.update()
        logout_modal.visible = True
        page.update()

    # Search and Filter Section
    search_filter_row = ft.Row(
        controls=[
            ft.TextField(
                hint_text="Search",
                width=300,
                prefix_icon=ft.Icons.SEARCH,
                border=ft.InputBorder.OUTLINE,
                filled=True,
                bgcolor="white"
            ),
            ft.ElevatedButton(
                "Filter",
                icon=ft.Icons.FILTER_LIST,
                style=ft.ButtonStyle(
                    bgcolor="#BB6F19",
                    color="white",
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    shape=ft.RoundedRectangleBorder(radius=8)
                )
            ),
            ft.Row(
                controls=[
                    ft.ElevatedButton("PDF", bgcolor="#BB6F19", color="white"),
                    ft.ElevatedButton("Excel", bgcolor="#BB6F19", color="white"),
                    ft.ElevatedButton("Print", bgcolor="#BB6F19", color="white"),
                ],
                spacing=10
            )
        ],
        alignment="spaceBetween",
        vertical_alignment="center",
        spacing=20
    )

    # Fetch transactions from the database
    def fetch_transactions():
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT t.transaction_id, t.order_code, t.total_amount,
                           GROUP_CONCAT(CONCAT(o.product_name, ' x', o.quantity, ' (₱', o.price, ')', 
                           IF(o.add_ons IS NOT NULL AND o.add_ons != '', CONCAT(' - Add-Ons: ', o.add_ons), '')) SEPARATOR '\n') AS orders
                    FROM transactions t
                    LEFT JOIN orders o ON o.transaction_id = t.transaction_id
                    GROUP BY t.transaction_id
                    ORDER BY t.transaction_id DESC
                """)
                transactions = cursor.fetchall()
                cursor.close()
                conn.close()
                return transactions
            else:
                print("Error: Unable to connect to the database.")
                return []
        except Exception as e:
            print(f"Error fetching transactions: {str(e)}")
            return []

    # Helper to build a transaction card
    def build_transaction_card(transaction):
        transaction_id = transaction[0]
        order_code = transaction[1]
        total_amount = float(transaction[2])
        orders_str = transaction[3] or ''
        order_lines = [line for line in orders_str.split('\n') if line.strip()]
        order_items = []
        for line in order_lines:
            parts = line.split(' x')
            if len(parts) >= 2:
                name = parts[0]
                qty_and_rest = parts[1]
                qty = qty_and_rest.split(' ')[0]
                order_items.append((name, qty))
            else:
                order_items.append((line, ''))
        col1 = order_items[::2]
        col2 = order_items[1::2]

        def on_card_click(e, order_code=order_code, page=page):
            receipts_dir = os.path.join(os.getcwd(), "receipts")
            pattern = os.path.join(receipts_dir, f"receipt_{order_code}_*.png")
            receipt_files = sorted(glob.glob(pattern), reverse=True)
            if receipt_files:
                receipt_img_path = receipt_files[0]
                receipt_img_src = receipt_img_path.replace(os.getcwd() + os.sep, "").replace("\\", "/")
                receipt_image = ft.Image(src=receipt_img_src, width=400, fit=ft.ImageFit.CONTAIN)
                receipt_modal = ft.Container(
                    visible=True,
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                    expand=True,
                    content=ft.Column(
                        controls=[
                            receipt_image,
                            ft.ElevatedButton(
                                "Close",
                                style=ft.ButtonStyle(
                                    bgcolor="#BB6F19",
                                    color="white",
                                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                                on_click=lambda e: (page.overlay.remove(receipt_modal), page.update(), remove_esc_handler()),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                )
                def esc_handler(e):
                    if e.key == "Escape":
                        if receipt_modal in page.overlay:
                            page.overlay.remove(receipt_modal)
                            page.update()
                            remove_esc_handler()
                def remove_esc_handler():
                    page.on_keyboard_event = None
                page.overlay.append(receipt_modal)
                page.on_keyboard_event = esc_handler
                page.update()
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("No receipt image found for this transaction."),
                    bgcolor="#F44336"
                )
                page.snack_bar.open = True
                page.update()

        def on_card_hover(e):
            if e.data == "true":
                e.control.bgcolor = "#F0E6D2"
                e.control.cursor = "pointer"
            else:
                e.control.bgcolor = "#F5F5F5"
                e.control.cursor = "default"
            e.control.update()

        def show_delete_transaction_confirmation(transaction_id=transaction_id):
            confirm_modal = ft.Container(
                visible=True,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                expand=True,
                content=ft.Container(
                    width=350,
                    height=160,
                    bgcolor="white",
                    border_radius=15,
                    padding=ft.padding.all(20),
                    content=ft.Column([
                        ft.Text("Delete Transaction", size=18, weight="bold", color="#E53935"),
                        ft.Text("Are you sure you want to delete this transaction and all its orders?", size=14, color="#333", text_align="center"),
                        ft.Row([
                            ft.ElevatedButton(
                                "Cancel",
                                style=ft.ButtonStyle(bgcolor="#E0E0E0", color="black"),
                                on_click=lambda e: (page.overlay.remove(confirm_modal), page.update()),
                            ),
                            ft.ElevatedButton(
                                "Delete",
                                style=ft.ButtonStyle(bgcolor="#E53935", color="white"),
                                on_click=lambda e: (page.overlay.remove(confirm_modal), delete_transaction_and_orders(transaction_id, page, refresh_transactions)),
                            ),
                        ], alignment="center", spacing=20),
                    ], spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ),
            )
            page.overlay.append(confirm_modal)
            page.update()

        orders_row = ft.Row([
            ft.Column([
                ft.Text(f"{name} x{qty}", size=12) for name, qty in col1
            ], spacing=2),
            ft.Column([
                ft.Text(f"{name} x{qty}", size=12) for name, qty in col2
            ], spacing=2),
        ], alignment="spaceBetween")

        return ft.Container(
            content=ft.Stack([
                ft.Column(
                    controls=[
                        ft.Text(f"Transaction ID: {transaction_id}", weight="bold", size=16),
                        ft.Text(f"Order Code: {order_code}", size=14),
                        ft.Text(f"Total: ₱{total_amount:.2f}", size=14),
                        ft.Divider(height=1, thickness=1, color="#BB6F19"),
                        ft.Text("Orders:", weight="bold", size=14),
                        orders_row,
                    ],
                    spacing=5
                ),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color="#E53935",
                        tooltip="Delete Transaction",
                        on_click=lambda e, transaction_id=transaction_id: show_delete_transaction_confirmation(transaction_id),
                    ),
                    alignment=ft.alignment.top_right,
                    padding=ft.padding.only(top=0, right=0),
                ),
            ]),
            width=300,
            height=200,
            bgcolor="#F5F5F5",
            border_radius=10,
            padding=10,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.1, "black")),
            on_hover=on_card_hover,
            on_click=lambda e, order_code=order_code: on_card_click(e, order_code, page),
        )

    # Function to refresh the transaction cards and update the UI
    def refresh_transactions():
        new_transactions = fetch_transactions()
        transaction_cards.clear()
        for transaction in new_transactions:
            transaction_cards.append(build_transaction_card(transaction))
        transactions_container.content.controls = transaction_cards
        page.update()

    transactions = fetch_transactions()

    # Create transaction cards using the helper
    transaction_cards = []
    for transaction in transactions:
        transaction_cards.append(build_transaction_card(transaction))

    # GridView to display transaction cards
    transactions_container = ft.Container(
        content=ft.GridView(
            controls=transaction_cards,
            max_extent=320,  # Width of each grid item
            spacing=20,  # Space between grid items
            run_spacing=20,  # Space between rows
            expand=True
        ),
        height=600,  # Increased height for better visibility
        bgcolor="white",
        border_radius=10,
        padding=10
    )

    def user_profile_card():
        user_id = page.session.get("user_id")
        full_name = get_employee_full_name(user_id)
        # If full_name is None or empty, fallback to 'Admin'
        if not full_name or full_name.lower() == 'none':
            # Try to fetch from admin table by username if possible
            try:
                conn = get_db_connection()
                if conn and conn.is_connected():
                    cursor = conn.cursor()
                    cursor.execute("SELECT full_name FROM admin WHERE id = %s", (user_id,))
                    row = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    if row and row[0]:
                        full_name = row[0]
                    else:
                        full_name = "Admin"
            except Exception:
                full_name = "Admin"
        return ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLACK),
                    bgcolor="#BB6F19",
                    radius=18
                ),
                ft.Column([
                    ft.Text(full_name, weight="bold", size=16, font_family="Poppins"),
                ], spacing=0),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color="black",
                    tooltip="Logout",
                    on_click=lambda e: handle_logout(page)
                )
            ], alignment="center", spacing=10),
            padding=10,
            border_radius=25,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )

    # Main layout
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Transactions", size=24, weight="bold", color="#BB6F19"),
                                ft.Text("Monday, 25 March 2025", size=14, color="black"),
                            ],
                            expand=True
                        ),
                        user_profile_card()  # Replace with the user_profile_card function
                    ],
                    alignment="spaceBetween",
                    vertical_alignment="center"
                ),
                ft.Divider(height=2, thickness=1, color="#BB6F19"),
                search_filter_row,
                transactions_container
            ],
            spacing=20
        ),
        padding=20,
        expand=True
    )