import flet as ft
import datetime
from config.database import get_db_connection, get_employee_full_name

def SummaryStatBox(icon, icon_color, title, value, change, change_color, change_text, subtext):
    return ft.Container(
        content=ft.Column([
            # Title row at the top
            ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(icon, color=icon_color, size=24),
                    bgcolor=ft.Colors.WHITE,
                    radius=20
                ),
                ft.Text(title, weight="bold", size=20, font_family="Poppins"),
            ], spacing=8, alignment="center", vertical_alignment="center"),
            
            # Spacer to push amount to center
            ft.Container(height=20),
            
            # Amount in the center
            ft.Text(value, size=36, weight="bold", font_family="Poppins", text_align="center"),
            
            # Spacer to push percentage to bottom
            ft.Container(height=20),
            
            # Percentage and text at the bottom
            ft.Column([
                ft.Container(
                    content=ft.Text(change, size=14, color=change_color, weight="bold"),
                    bgcolor=ft.Colors.GREEN_100 if change_color == ft.Colors.GREEN_700 else ft.Colors.RED_100,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    alignment=ft.alignment.center
                ),
                ft.Text(change_text, size=12, color=ft.Colors.GREY_700),
                ft.Text(subtext, size=12, color=ft.Colors.GREY_700, text_align="left"),
            ], alignment="start", spacing=4),
        ], alignment="center", spacing=2, horizontal_alignment="center"),
        padding=16,
        bgcolor=ft.Colors.WHITE,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.BLACK),
        shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
        expand=True,
        height=230,
        width=300
    )

def dashboard_view(page: ft.Page):
    today = datetime.datetime.now()
    day_str = today.strftime('%A')
    date_str = today.strftime('%d %B %Y')

    # Fetch dynamic data
    def fetch_dashboard_data():
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()

                # Fetch revenue, profit, and total orders for today
                cursor.execute("""
                    SELECT 
                        SUM(price) AS revenue, 
                        SUM(price * 0.4) AS profit, 
                        COUNT(*) AS total_orders 
                    FROM orders 
                    WHERE DATE(created_at) = CURDATE() AND status = 'Confirmed'
                """)
                today_data = cursor.fetchone()
                revenue_today = today_data[0] or 0
                profit_today = today_data[1] or 0
                total_orders_today = today_data[2] or 0

                # Fetch revenue, profit, and total orders for yesterday
                cursor.execute("""
                    SELECT 
                        SUM(price) AS revenue, 
                        SUM(price * 0.4) AS profit, 
                        COUNT(*) AS total_orders 
                    FROM orders 
                    WHERE DATE(created_at) = CURDATE() - INTERVAL 1 DAY AND status = 'Confirmed'
                """)
                yesterday_data = cursor.fetchone()
                revenue_yesterday = yesterday_data[0] or 0
                profit_yesterday = yesterday_data[1] or 0
                total_orders_yesterday = yesterday_data[2] or 0

                # Calculate percentage changes
                revenue_change = ((revenue_today - revenue_yesterday) / revenue_yesterday * 100) if revenue_yesterday else 0
                profit_change = ((profit_today - profit_yesterday) / profit_yesterday * 100) if profit_yesterday else 0
                total_orders_change = ((total_orders_today - total_orders_yesterday) / total_orders_yesterday * 100) if total_orders_yesterday else 0

                # Fetch product with the highest orders
                cursor.execute("""
                    SELECT 
                        product_name, 
                        COUNT(*) AS orders_count 
                    FROM orders 
                    WHERE status = 'Confirmed' 
                    GROUP BY product_name 
                    ORDER BY orders_count DESC 
                    LIMIT 4
                """)
                top_products = cursor.fetchall()

                cursor.close()
                conn.close()

                return {
                    "revenue_today": revenue_today,
                    "profit_today": profit_today,
                    "total_orders_today": total_orders_today,
                    "revenue_change": revenue_change,
                    "profit_change": profit_change,
                    "total_orders_change": total_orders_change,
                    "top_products": top_products
                }
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
            return {
                "revenue_today": 0,
                "profit_today": 0,
                "total_orders_today": 0,
                "revenue_change": 0,
                "profit_change": 0,
                "total_orders_change": 0,
                "top_products": []
            }

    dashboard_data = fetch_dashboard_data()

    def product_table(products):
        rows = [
            ft.Row([
                ft.Container(ft.Text("Name", weight="bold", size=14), width=140, alignment=ft.alignment.center_left),
                ft.Container(ft.Text("Orders", weight="bold", size=14), width=80, alignment=ft.alignment.center),
            ], spacing=10, alignment="center")
        ]
        for product in products:
            rows.append(
                ft.Row([
                    ft.Container(
                        ft.Text(product[0], size=14, font_family="Poppins"),
                        width=140, alignment=ft.alignment.center_left
                    ),
                    ft.Container(
                        ft.Text(str(product[1]), size=14, font_family="Poppins"),
                        width=80, alignment=ft.alignment.center
                    ),
                ], spacing=10, alignment="center")
            )
        return rows

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

    def user_profile_card():
        user_id = page.session.get("user_id")
        full_name = get_employee_full_name(user_id)
        if not full_name or full_name.lower() == 'none':
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

    def handle_logout(page):
        # Create a custom modal dialog for logout confirmation
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

        # Add the modal to the page overlay
        page.overlay.append(logout_modal)

        def confirm_logout():
            logout_modal.visible = False  # Hide the modal
            page.overlay.remove(logout_modal)  # Remove the modal from the overlay
            page.update()  # Update the page to reflect changes
            page.clean()  # Clear all existing UI elements
            page.bgcolor = "white"  # Reset the background color to white
            from views.login import main
            main(page)  # Redirect to the login window
            page.update()

        def close_logout_modal():
            logout_modal.visible = False  # Hide the modal
            page.overlay.remove(logout_modal)  # Remove the modal from the overlay
            page.update()  # Update the page to reflect changes

        # Show the modal
        logout_modal.visible = True
        page.update()

    def get_top_beverages():
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()
                # Get top 4 products by stock (as a simple example)
                cursor.execute("""
                    SELECT product_id, name, type, price, availability, image_path 
                    FROM products 
                    ORDER BY availability DESC 
                    LIMIT 4
                """)
                products = cursor.fetchall()
                cursor.close()
                conn.close()
                return products
            return []
        except Exception as e:
            print(f"Error fetching top beverages: {e}")
            return []

    def beverage_table(products):
        header = ft.Row([
            ft.Container(width=48),  # For image
            ft.Container(width=110, content=ft.Text("", size=14)),  # For name
            ft.Container(width=60, content=ft.Text("Price", size=14, weight="bold", text_align="center")),
            ft.Container(width=60, content=ft.Text("Availability", size=14, weight="bold", text_align="center")),
        ], spacing=0, alignment="end")
        rows = [header]
        
        for product in products:
            # Use a default image if the product image is not available
            image_path = product[5] if product[5] else "icons/default_product.png"
            rows.append(
                ft.Row([
                    ft.Container(
                        content=ft.Image(
                            src=image_path,
                            width=40,
                            height=40,
                            fit=ft.ImageFit.CONTAIN,
                            error_content=ft.Icon(ft.Icons.ERROR, color=ft.Colors.GREY)
                        ),
                        width=48,
                        alignment=ft.alignment.center_left
                    ),
                    ft.Container(
                        content=ft.Text(product[1], weight="bold", size=15, font_family="Poppins"),
                        width=110,
                        alignment=ft.alignment.center_left
                    ),
                    ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                    ft.Container(
                        content=ft.Text(f"₱{product[3]:.2f}", size=15, font_family="Poppins", text_align="center"),
                        width=60,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(
                        content=ft.Text(str(product[4]), size=15, font_family="Poppins", text_align="center"),
                        width=60,
                        alignment=ft.alignment.center
                    ),
                ], spacing=0, alignment="end")
            )
        return rows

    # Get top beverages from database
    top_beverages = get_top_beverages()

    # Fetch logged-in user's first name
    def get_logged_in_user_first_name():
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("SELECT first_name FROM employees WHERE id = %s", (page.session.get("user_id"),))
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                return user[0] if user else "User"
        except Exception as e:
            print(f"Error fetching user first name: {e}")
            return "User"

    first_name = get_logged_in_user_first_name()

    # Main layout
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text("Dashboard", size=24, weight="bold", color="#BB6F19"),
                                ft.Text(
                                    spans=[
                                        ft.TextSpan(day_str + ", ", style=ft.TextStyle(weight="bold")),
                                        ft.TextSpan(date_str)
                                    ],
                                    size=14
                                ),
                            ],
                            expand=True
                        ),
                        user_profile_card()
                    ],
                    alignment="spaceBetween",
                    vertical_alignment="center"
                ),
                ft.Divider(height=2, thickness=1, color="#BB6F19"),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Summary", weight="bold", size=16, font_family="Poppins"),
                            ft.Row(
                                controls=[
                                    SummaryStatBox(
                                        icon=ft.Icons.PAID,
                                        icon_color=ft.Colors.GREEN_700,
                                        title="Total Revenue",
                                        value=f"₱{dashboard_data['revenue_today']:.2f}",
                                        change=f"▲ {dashboard_data['revenue_change']:.2f}%",
                                        change_color=ft.Colors.GREEN_700 if dashboard_data['revenue_change'] >= 0 else ft.Colors.RED_700,
                                        change_text="vs yesterday",
                                        subtext=""
                                    ),
                                    SummaryStatBox(
                                        icon=ft.Icons.ATTACH_MONEY,
                                        icon_color=ft.Colors.BLUE_700,
                                        title="Total Profit",
                                        value=f"₱{dashboard_data['profit_today']:.2f}",
                                        change=f"▲ {dashboard_data['profit_change']:.2f}%",
                                        change_color=ft.Colors.GREEN_700 if dashboard_data['profit_change'] >= 0 else ft.Colors.RED_700,
                                        change_text="vs yesterday",
                                        subtext=""
                                    ),
                                    SummaryStatBox(
                                        icon=ft.Icons.SHOPPING_BAG,
                                        icon_color=ft.Colors.ORANGE_700,
                                        title="Total Orders",
                                        value=str(dashboard_data['total_orders_today']),
                                        change=f"▲ {dashboard_data['total_orders_change']:.2f}%",
                                        change_color=ft.Colors.GREEN_700 if dashboard_data['total_orders_change'] >= 0 else ft.Colors.RED_700,
                                        change_text="vs yesterday",
                                        subtext=""
                                    ),
                                ],
                                spacing=20,
                                alignment="center"
                            ),
                        ],
                        spacing=20
                    ),
                    bgcolor="#F5E9DA",
                    border_radius=12,
                    padding=16,
                    margin=ft.margin.only(top=10, bottom=10),
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Row(
                                            controls=[
                                                ft.Column(
                                                    controls=[
                                                        ft.Text(f"Hi, {first_name}", weight="bold", size=18, font_family="Poppins"),
                                                        ft.Text(
                                                            "Ready to kick off your day of serving\ngreat coffee?",
                                                            size=12,
                                                            color=ft.Colors.GREY_700,
                                                            font_family="Poppins"
                                                        ),
                                                        ft.Container(
                                                            content=ft.ElevatedButton(
                                                                "Start POS",
                                                                style=ft.ButtonStyle(
                                                                    bgcolor="#E9CBA7",
                                                                    color=ft.Colors.BLACK,
                                                                    padding=ft.padding.symmetric(horizontal=40, vertical=16),
                                                                    shape=ft.RoundedRectangleBorder(radius=8),
                                                                    text_style=ft.TextStyle(size=20, weight="bold", font_family="Poppins")
                                                                ),
                                                                icon=ft.Icons.POINT_OF_SALE
                                                            ),
                                                            margin=ft.margin.only(top=12)
                                                        ),
                                                    ],
                                                    spacing=4,
                                                    alignment="start"
                                                ),
                                                ft.Container(
                                                    content=ft.Image(src="icons/coffee_icon.png", width=120, height=120, fit=ft.ImageFit.CONTAIN),
                                                    alignment=ft.alignment.center,
                                                    margin=ft.margin.only(left=3)
                                                ),
                                            ],
                                            alignment="center",
                                            vertical_alignment="center",
                                            spacing=12
                                        ),
                                        bgcolor=ft.Colors.WHITE,
                                        border_radius=12,
                                        padding=16,
                                        margin=ft.margin.only(bottom=10),
                                        shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
                                        width=450,
                                        height=250  # Reduced height from 300 to 250
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            '"Delivering happiness, one freshly brewed cup at a time."',
                                            size=14,
                                            color="#BB6F19",
                                            italic=True,
                                            font_family="Poppins"
                                        ),
                                        bgcolor=ft.Colors.WHITE,
                                        border_radius=12,
                                        padding=16,
                                        shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
                                    )
                                ]
                            ),
                            expand=True,
                            width=450,
                            height=250,  # Adjusted height to match the container
                            margin=ft.margin.only(right=20)
                        ),
                        ft.Container(
                            bgcolor="white",
                            border_radius=12,
                            padding=16,
                            width=700,
                            height=300,
                            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
                            content=ft.Column(
                                controls=[
                                    ft.Text("Top Products", weight="bold", size=18, font_family="Poppins"),
                                    ft.Text("Most ordered items", size=12, color=ft.Colors.GREY_700),
                                    ft.Container(
                                        content=ft.Column(
                                            controls=product_table(dashboard_data['top_products']),
                                            spacing=8
                                        ),
                                        bgcolor=ft.Colors.GREY_100,
                                        border_radius=8,
                                        padding=10,
                                        margin=ft.margin.only(top=10, bottom=10)
                                    ),
                                ],
                                spacing=20  # Adjust spacing for better alignment
                            )
                        )
                    ],
                    spacing=20
                ),
            ],
            spacing=20
        ),
        padding=20,
        expand=True
    )

    # Add the content to the page
    page.add(main_content)
    page.update()