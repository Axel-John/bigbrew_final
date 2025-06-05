import flet as ft
from flet import Page, Row, Column, Container, Text, TextField, ElevatedButton, IconButton, alignment, border_radius, padding, TextButton
from config.database import get_db_connection
from utils.auth import hash_password

# This is the login screen function
# It is designed to be called from main.py using: from login import main as login_page

def main(page: Page):
    # Set page properties
    page.title = "BigBrew - Login"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.padding = 0
    page.window_width = 1000
    page.window_height = 700
    page.expand = True  # Ensure the page itself expands to fill the screen
    page.fonts = {
        "Poppins": "assets/fonts/Poppins-Regular.ttf",
        "Poppins-Bold": "assets/fonts/Poppins-Bold.ttf",
    }
    page.route = "/login"  # Set the current route

    def handle_keyboard(e):
        # Ensure the shortcut only works on the login window
        if page.route == "/login" and page.title == "BigBrew - Login":
            # Check for Ctrl+Alt+A using key combination
            if e.key.lower() == "a" and e.ctrl and e.alt:
                print("Admin shortcut detected!")
                page.clean()
                from views.admin_login import admin_login
                admin_login(page)
                page.update()

    page.on_keyboard_event = handle_keyboard

    # Create form fields first
    employee_id_field = TextField(
        label="Employee ID",
        width=300,
        prefix_icon="person",
        border_color="black",
        helper_text="Format: EMPxxx (e.g., EMP001)",
        helper_style=ft.TextStyle(
            color="black"
        ),
        focused_border_color="#BA6F1B",
        cursor_color="#BA6F1B",
        label_style=ft.TextStyle(
            color="rgba(0, 0, 0, 0.5)"
        ),
        bgcolor="white",
        border=ft.border.all(1, "black"),
        border_radius=4,
        text_size=14,
    )
    
    password_field = TextField(
        label="Password",
        width=300,
        password=True,
        can_reveal_password=True,
        prefix_icon="lock",
        border_color="black",
        focused_border_color="#BA6F1B",
        cursor_color="#BA6F1B",
        label_style=ft.TextStyle(
            color="rgba(0, 0, 0, 0.5)"
        ),
        bgcolor="white",
        border=ft.border.all(1, "black"),
        border_radius=4,
    )

    error_text = Text(
        value="",
        color="red",
        size=12,
        visible=False
    )

    def handle_login(e):
        # Reset error message
        error_text.visible = False
        
        # Validate input format
        emp_id_or_email = employee_id_field.value.strip()
        password = password_field.value

        if not emp_id_or_email or not password:
            error_text.value = "Please fill in all fields"
            error_text.visible = True
            page.update()
            return

        # Determine if input is email or employee_id
        is_email = '@' in emp_id_or_email
        emp_id_check = emp_id_or_email.upper()
        if not is_email:
            if not emp_id_check.startswith("EMP") or not emp_id_check[3:].isdigit():
                error_text.value = "Invalid Employee ID format. Use format: EMPxxxx or enter your email."
                error_text.visible = True
                page.update()
                return

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            # Get employee with matching ID or email
            if is_email:
                cursor.execute("""
                    SELECT id, first_name, last_name, password 
                    FROM employees 
                    WHERE email = %s
                """, (emp_id_or_email,))
            else:
                cursor.execute("""
                    SELECT id, first_name, last_name, password 
                    FROM employees 
                    WHERE employee_id = %s
                """, (emp_id_check,))
            
            result = cursor.fetchone()
            
            if not result:
                error_text.value = "Invalid Employee ID or Email"
                error_text.visible = True
                page.update()
                return

            # Verify password
            hashed_password = hash_password(password)
            if hashed_password != result[3]:
                error_text.value = "Invalid password"
                error_text.visible = True
                page.update()
                return

            # Login successful
            error_text.value = f"Logging in as {result[1]} {result[2]}"
            error_text.color = "green"
            error_text.visible = True
            # Clear fields
            employee_id_field.value = ""
            password_field.value = ""
            
            page.update()

            # Redirect to order window after a short delay (non-blocking)
            def go_to_order_window():
                page.clean()
                from views.order_window import main as order_window_main
                order_window_main(page)  # Redirect to the order window
                page.update()

            import threading
            threading.Timer(1.0, go_to_order_window).start()  # Redirect after a short delay

        except Exception as e:
            error_text.value = f"Error during login: {str(e)}"
            error_text.visible = True
            page.update()
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def handle_forgot_password(e):
        print("Forgot Password clicked")

    # Left container with coffee theme
    left_container = Container(
        width=400,
        height=600,
        bgcolor="#E6E6EF",  # Light grayish-blue color
        padding=padding.all(40),
        border=ft.border.all(1, "#E6E6EF"),  # Matching border color
        content=Column(
            horizontal_alignment="center",
            alignment="center",
            controls=[
                Text(
                    value="Coffee That Brings You\nComfort, One Cup at a\nTime",
                    size=25,
                    color="#BB6F19",
                    font_family="Poppins-Bold",
                    text_align="left",
                    weight="w900"
                ),
                Container(
                    margin=padding.only(top=30),
                    content=ft.Image(src="assets/images/coffee_cup.png", width=300, height=300, fit=ft.ImageFit.CONTAIN)
                ),
                Container(height=40),
                Row(
                    alignment="center",
                    controls=[
                        Text(
                            value="Don't have an account? Bleeee",
                            color="black",
                            size=14,
                        ),
                    ]
                )
            ]
        )
    )

    # Right container with login form
    right_container = Container(
        width=400,
        height=600,
        bgcolor="#BA6F1B",  # Coffee Brown
        padding=padding.all(40),
        content=Column(
            horizontal_alignment="center",
            alignment="center",
            controls=[
                Column(
                    horizontal_alignment="center",
                    spacing=0,
                    controls=[
                        ft.Image(src="assets/images/bigbrew_logo_black.png", width=120, height=90, fit=ft.ImageFit.CONTAIN),
                        Text(
                            value="BigBrew",
                            size=40,
                            color="black",
                            weight="bold",
                            font_family="Poppins-Bold"
                        ),
                    ]
                ),
                Container(
                    padding=padding.only(top=20, bottom=20),
                    content=Column(
                        horizontal_alignment="center",
                        controls=[
                            Text(
                                value="Welcome back!",
                                size=18,
                                color="black",
                                font_family="Poppins-Bold",
                                text_align="center",
                                weight="w900"
                            ),
                            Text(
                                value="Log in to your account and start brewing.",
                                size=14,
                                color="black",
                                opacity=0.9
                            )
                        ],
                        spacing=5
                    )
                ),
                employee_id_field,
                Container(height=5),
                password_field,
                Row(
                    spacing=0,
                    alignment="end",
                    controls=[
                        TextButton(
                            text="Forgot password?",
                            on_click=handle_forgot_password,
                            style=ft.ButtonStyle(
                                color={"": "black", "hovered": "blue"},
                            ),
                        ),
                    ]
                ),
                Container(height=1),
                error_text,
                Container(height=2),
                ElevatedButton(
                    text="Log in",
                    width=150,
                    on_click=handle_login,
                    color="#FFFFFF",
                    bgcolor="black",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10)
                    )
                )
            ]
        )
    )

    # Wrap everything in a Stack to layer the background image
    page.add(
        ft.Stack(
            expand=True,  # Ensure the stack fills the entire screen
            controls=[
                ft.Image(
                    src="assets/images/bg.png",  # Use the provided background photo
                    fit=ft.ImageFit.NONE,  # Disable automatic scaling
                    width=1930,  # Set the width to 1950 to cover the full screen
                    expand=False,  # Ensure the image expands to fit the screen
                ),
                Container(
                    expand=True,  # Ensure the main container expands to fit the screen
                    alignment=alignment.center,  # Center the content
                    content=Container(
                        width=800,
                        height=600,
                        alignment=alignment.center,
                        content=Row(
                            alignment="center",
                            vertical_alignment="center",
                            controls=[
                                left_container,
                                right_container
                            ],
                            spacing=0
                        )
                    )
                )
            ]
        )
    )
    page.update()
