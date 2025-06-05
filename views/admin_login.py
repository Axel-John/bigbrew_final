import flet as ft
from flet import Page, Row, Column, Container, Text, TextField, ElevatedButton, TextButton, alignment, padding
from config.database import get_db_connection
from utils.auth import hash_password

def admin_login(page: Page):
    # Set page properties
    page.title = "BigBrew - Admin Login"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.expand = True  # Ensure the page itself expands to fill the screen
    page.window_width = 1000
    page.window_height = 700
    page.fonts = {
        "Poppins": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf",
        "Poppins-Bold": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf",
    }

    # Form fields
    username_field = TextField(
        label="Username",
        width=300,
        prefix_icon="person",
        border_color="black",
        focused_border_color="#BA6F1B",
        cursor_color="#BA6F1B",
        label_style=ft.TextStyle(
            color="rgba(0, 0, 0, 0.5)"
        ),
        bgcolor="white",
        border=ft.border.all(1, "black"),
        border_radius=8,  # Added border radius
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
        border_radius=8,  # Added border radius
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
        
        # Get input values
        username = username_field.value
        password = password_field.value

        if not username or not password:
            error_text.value = "Please fill in all fields"
            error_text.visible = True
            page.update()
            return

        try:
            connection = get_db_connection()
            if connection is None:
                error_text.value = "Error connecting to database. Please check if XAMPP is running."
                error_text.visible = True
                page.update()
                return

            cursor = connection.cursor()

            # Get admin with matching username
            cursor.execute("""
                SELECT id, full_name, password 
                FROM admin 
                WHERE username = %s
            """, (username,))
            
            result = cursor.fetchone()
            
            if not result:
                error_text.value = "Invalid username"
                error_text.visible = True
                page.update()
                return

            # Verify password
            hashed_password = hash_password(password)
            if hashed_password != result[2]:
                error_text.value = "Invalid password"
                error_text.visible = True
                page.update()
                return

            # Login successful
            error_text.value = f"Welcome back, {result[1]}!"
            error_text.color = "green"
            error_text.visible = True
            
            # Clear fields
            username_field.value = ""
            password_field.value = ""
            
            # Navigate to main layout
            page.clean()
            from views.main_layout import main
            main(page)
            page.update()

        except Exception as e:
            error_text.value = f"Error during login: {str(e)}"
            error_text.visible = True
            page.update()
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def handle_back(e):
        page.clean()
        from views.login import main
        main(page)
        page.update()

    # Main container
    main_container = Container(
        width=400,
        height=600,
        border_radius=20,
        bgcolor="#BA6F1B",
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
                            value="BigBrew Admin",
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
                                value="Admin Login",
                                size=18,
                                color="black",
                                font_family="Poppins-Bold",
                                text_align="center",
                                weight="w900"
                            ),
                            Text(
                                value="Enter your admin credentials",
                                size=14,
                                color="black",
                                opacity=0.9
                            )
                        ],
                        spacing=5
                    )
                ),
                username_field,
                Container(height=5),
                password_field,
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
                ),
                Container(height=20),
                TextButton(
                    text="Back to Employee Login",
                    on_click=handle_back,
                    style=ft.ButtonStyle(
                        color={"": "black", "hovered": "blue"},
                    ),
                )
            ]
        )
    )

    # Add to page
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
                    content=main_container
                )
            ]
        )
    )
    page.update()