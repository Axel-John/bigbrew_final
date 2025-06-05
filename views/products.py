import flet as ft
from config.database import get_db_connection
import os
from datetime import datetime
import threading  # Import threading for Timer

CATEGORIES = ["All", "Milk Tea", "Iced Coffee", "Fruit Tea", "Hot Brew"]

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

# Define page globally at the top of the file
page = None  # Placeholder for the Page object, will be set in products_view()

def products_view(page_obj: ft.Page):
    global page
    page = page_obj  # Set the global page object

    # Initialize product_id_to_edit in the outer scope
    product_id_to_edit = None

    # Form fields for Add Product Modal
    add_name_field = ft.TextField(
        label="Product Name",
        border=ft.InputBorder.OUTLINE,
        width=300,
        autofocus=True,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )
    
    add_type_dropdown = ft.Dropdown(
        label="Product Type",
        options=[
            ft.dropdown.Option("Milk Tea"),
            ft.dropdown.Option("Iced Coffee"),
            ft.dropdown.Option("Fruit Tea"),
            ft.dropdown.Option("Hot Brew")
        ],
        width=300,
        border=ft.InputBorder.OUTLINE,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )
    
    add_price_field = ft.TextField(
        label="Price",
        border=ft.InputBorder.OUTLINE,
        width=300,
        prefix_text="₱",
        keyboard_type=ft.KeyboardType.NUMBER,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )
    
    add_availability_dropdown = ft.Dropdown(
        label="Availability",
        options=[
            ft.dropdown.Option("Available"),
            ft.dropdown.Option("Limited"),
            ft.dropdown.Option("Out of Order")
        ],
        width=300,
        border=ft.InputBorder.OUTLINE,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )

    # Form fields for Edit Product Modal
    edit_name_field = ft.TextField(
        label="Product Name",
        border=ft.InputBorder.OUTLINE,
        width=300,
        autofocus=True,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )
    
    edit_type_dropdown = ft.Dropdown(
        label="Product Type",
        options=[
            ft.dropdown.Option("Milk Tea"),
            ft.dropdown.Option("Iced Coffee"),
            ft.dropdown.Option("Fruit Tea"),
            ft.dropdown.Option("Hot Brew")
        ],
        width=300,
        border=ft.InputBorder.OUTLINE,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )
    
    edit_price_field = ft.TextField(
        label="Price",
        border=ft.InputBorder.OUTLINE,
        width=300,
        prefix_text="₱",
        keyboard_type=ft.KeyboardType.NUMBER,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )
    
    edit_availability_dropdown = ft.Dropdown(
        label="Availability",
        options=[
            ft.dropdown.Option("Available"),
            ft.dropdown.Option("Limited"),
            ft.dropdown.Option("Out of Order")
        ],
        width=300,
        border=ft.InputBorder.OUTLINE,
        filled=True,
        bgcolor=ft.Colors.WHITE
    )

    error_text = ft.Text("", color=ft.Colors.RED, size=12)
    success_text = ft.Text("", color=ft.Colors.GREEN, size=12)

    # Adjusted form fields layout for Add Modal
    add_type_price_row = ft.Row(
        controls=[
            ft.Container(
                content=add_type_dropdown,
                width=180
            ),
            ft.Container(
                content=add_price_field,
                width=120
            )
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START
    )

    # Adjusted form fields layout for Edit Modal
    edit_type_price_row = ft.Row(
        controls=[
            ft.Container(
                content=edit_type_dropdown,
                width=180
            ),
            ft.Container(
                content=edit_price_field,
                width=120
            )
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.START
    )

    def clear_add_form_fields():
        # Clear all add form fields
        add_name_field.value = ""
        add_type_dropdown.value = None
        add_price_field.value = ""
        add_availability_dropdown.value = None
        error_text.value = ""
        success_text.value = ""
        # Reset photo preview and upload status
        add_photo_preview.content = None
        add_photo_preview.visible = True
        nonlocal add_uploaded_photo_path
        add_uploaded_photo_path = None
        add_photo_upload_status.value = ""
        add_photo_upload_status.visible = True

    def show_add_product_form(e):
        # Always start with empty form
        clear_add_form_fields()
        # Show the modal
        add_product_modal.visible = True
        page.update()

    def close_add_product_dialog(e=None):
        # Clear all fields when closing add modal
        clear_add_form_fields()
        add_product_modal.visible = False
        page.update()

    def save_product(e):
        # Validate required fields
        if not all([add_name_field.value, add_type_dropdown.value, add_price_field.value, add_availability_dropdown.value]):
            error_text.value = "Please fill in all fields."
            success_text.value = ""
            error_text.visible = True
            success_text.visible = False
            page.update()
            return

        # Ensure photo is uploaded
        if not add_uploaded_photo_path:
            error_text.value = "Please upload a product image."
            success_text.value = ""
            error_text.visible = True
            success_text.visible = False
            page.update()
            return

        try:
            # Generate product ID based on type with a 3-digit unique identifier
            type_prefix = {
                "Milk Tea": "MT",
                "Iced Coffee": "IC",
                "Fruit Tea": "FT",
                "Hot Brew": "HB"
            }.get(add_type_dropdown.value, "OT")  # Default to "OT" for other types

            # Fetch the current highest product ID for the given type
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT MAX(CAST(SUBSTRING(product_id, 4) AS UNSIGNED)) FROM products WHERE product_id LIKE '{type_prefix}-%'"
                )
                max_id = cursor.fetchone()[0]
                next_id = (max_id + 1) if max_id else 1
                product_id = f"{type_prefix}-{next_id:03d}"  # Format as 3-digit ID

                # Get the relative path for database storage
                relative_path = os.path.relpath(add_uploaded_photo_path)
                print(f"Saving image path to database: {relative_path}")  # Debug print

                # Save to database with the image path
                cursor.execute(
                    """
                    INSERT INTO products (product_id, name, type, price, availability, image_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        product_id,
                        add_name_field.value,
                        add_type_dropdown.value,
                        float(add_price_field.value),
                        add_availability_dropdown.value,
                        relative_path  # Store the relative path
                    )
                )
                conn.commit()
                cursor.close()
                conn.close()

                # Clear form fields BEFORE showing success modal
                clear_add_form_fields()

                # Create success message container
                success_container = ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,  # Adjusted spacing for better layout
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE,
                                size=60,  # Increased icon size for better visibility
                                color=ft.Colors.GREEN
                            ),
                            ft.Text(
                                "Product Added Successfully!",
                                size=22,  # Increased text size for emphasis
                                weight=ft.FontWeight.BOLD,
                                color="#BB6F19",
                                text_align=ft.TextAlign.CENTER  # Centered text alignment
                            ),
                            ft.Text(
                                "Your product has been added to the inventory.",
                                size=14,
                                color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER  # Centered text alignment
                            ),
                            ft.ElevatedButton(
                                "OK",
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor="#BB6F19",
                                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                                on_click=lambda e: close_success_and_form()
                            )
                        ]
                    ),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,  # Increased border radius for rounded corners
                    width=350,  # Adjusted width for better layout
                    height=200,  # Adjusted height for better layout
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                        offset=ft.Offset(0, 3)
                    )
                )

                # Create success modal
                success_modal = ft.Container(
                    visible=True,
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                    expand=True,
                    content=success_container
                )

                def close_success_and_form():
                    # Hide modals
                    success_modal.visible = False
                    add_product_modal.visible = False
                    # Remove success modal from overlay
                    if success_modal in page.overlay:
                        page.overlay.remove(success_modal)
                    # Update page and refresh table
                    page.update()
                    refresh_table()

                # Add success modal to page overlay
                page.overlay.append(success_modal)
                page.update()

            else:
                error_text.value = "Unable to connect to the database."
                success_text.value = ""
                error_text.visible = True
                success_text.visible = False
                page.update()
        except ValueError as ve:
            error_text.value = "Please enter a valid price."
            success_text.value = ""
            error_text.visible = True
            success_text.visible = False
            page.update()
            print(f"Value error: {str(ve)}")
        except Exception as e:
            error_text.value = "An error occurred while saving the product."
            success_text.value = ""
            error_text.visible = True
            success_text.visible = False
            page.update()
            print(f"Error saving product: {str(e)}")

    # Separate photo preview and status for add and edit modals
    add_uploaded_photo_path = None
    add_photo_preview = ft.Container(
        content=None,
        border_radius=8,
        border=ft.border.all(1, ft.Colors.GREY_300),
        margin=ft.margin.only(bottom=10),
        alignment=ft.alignment.center,
        width=110,
        height=110,
        visible=True
    )
    add_photo_upload_status = ft.Text(
        "",
        size=12,
        color=ft.Colors.GREY,
        text_align=ft.TextAlign.CENTER,
        visible=True
    )

    edit_uploaded_photo_path = None
    edit_photo_preview = ft.Container(
        content=None,
        border_radius=8,
        border=ft.border.all(1, ft.Colors.GREY_300),
        margin=ft.margin.only(bottom=10),
        alignment=ft.alignment.center,
        width=110,
        height=110,
        visible=True
    )
    edit_photo_upload_status = ft.Text(
        "",
        size=12,
        color=ft.Colors.GREY,
        text_align=ft.TextAlign.CENTER,
        visible=True
    )

    # Add modal upload handler
    def handle_add_photo_upload(file):
        nonlocal add_uploaded_photo_path
        if file:
            try:
                os.makedirs("uploads", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = os.path.splitext(file.name)[1]
                new_filename = f"{timestamp}{file_extension}"
                add_uploaded_photo_path = os.path.join("uploads", new_filename)
                abs_upload_path = os.path.abspath(add_uploaded_photo_path)
                with open(abs_upload_path, "wb") as f:
                    with open(file.path, "rb") as source_file:
                        f.write(source_file.read())
                add_photo_upload_status.value = f"Uploaded: {file.name}"
                add_photo_upload_status.color = ft.Colors.GREY
                add_photo_upload_status.visible = True
                add_photo_preview.content = ft.Image(
                    src=abs_upload_path,
                    width=100,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=8,
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    gapless_playback=True
                )
                add_photo_preview.visible = True
                page.update()
            except Exception as e:
                add_photo_preview.content = None
                add_photo_upload_status.value = "Error uploading image"
                add_photo_upload_status.color = ft.Colors.RED
                add_photo_upload_status.visible = True
                page.update()
        else:
            add_photo_preview.content = None
            add_photo_upload_status.value = ""
            add_photo_upload_status.visible = True
            page.update()

    # Edit modal upload handler
    def handle_edit_photo_upload(file):
        nonlocal edit_uploaded_photo_path
        if file:
            try:
                os.makedirs("uploads", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = os.path.splitext(file.name)[1]
                new_filename = f"{timestamp}{file_extension}"
                edit_uploaded_photo_path = os.path.join("uploads", new_filename)
                abs_upload_path = os.path.abspath(edit_uploaded_photo_path)
                with open(abs_upload_path, "wb") as f:
                    with open(file.path, "rb") as source_file:
                        f.write(source_file.read())
                edit_photo_upload_status.value = f"Uploaded: {file.name}"
                edit_photo_upload_status.color = ft.Colors.GREY
                edit_photo_upload_status.visible = True
                edit_photo_preview.content = ft.Image(
                    src=abs_upload_path,
                    width=100,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=8,
                    repeat=ft.ImageRepeat.NO_REPEAT,
                    gapless_playback=True
                )
                edit_photo_preview.visible = True
                page.update()
            except Exception as e:
                edit_photo_preview.content = None
                edit_photo_upload_status.value = "Error uploading image"
                edit_photo_upload_status.color = ft.Colors.RED
                edit_photo_upload_status.visible = True
                page.update()
        else:
            edit_photo_preview.content = None
            edit_photo_upload_status.value = ""
            edit_photo_upload_status.visible = True
            page.update()

    # Separate file pickers for add and edit
    add_file_picker = ft.FilePicker(
        on_result=lambda result: handle_add_photo_upload(result.files[0]) if result.files else None
    )
    page.overlay.append(add_file_picker)

    edit_file_picker = ft.FilePicker(
        on_result=lambda result: handle_edit_photo_upload(result.files[0]) if result.files else None
    )
    page.overlay.append(edit_file_picker)

    def add_upload_photo(e):
        nonlocal add_uploaded_photo_path
        add_file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["png", "jpg", "jpeg"],
            dialog_title="Select Product Image"
        )

    def edit_upload_photo(e):
        nonlocal edit_uploaded_photo_path
        edit_file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["png", "jpg", "jpeg"],
            dialog_title="Select Product Image"
        )

    # Add modal photo upload section
    add_photo_upload_section = ft.Column(
        spacing=15,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("Product Image", size=16, weight=ft.FontWeight.BOLD, color="#BB6F19"),
            ft.Container(
                content=add_photo_preview,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=5,
                alignment=ft.alignment.center,
                width=110,
                height=110
            ),
            ft.ElevatedButton(
                "Upload Photo",
                icon=ft.Icons.UPLOAD,
                on_click=add_upload_photo,
                style=ft.ButtonStyle(
                    bgcolor="#BB6F19",
                    color=ft.Colors.WHITE,
                    padding=ft.padding.symmetric(horizontal=20, vertical=10)
                )
            ),
            ft.Container(
                content=add_photo_upload_status,
                padding=ft.padding.symmetric(vertical=5),
                alignment=ft.alignment.center
            ),
        ],
        expand=True,
    )

    # Edit modal photo upload section
    edit_photo_upload_section = ft.Column(
        spacing=15,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("Product Image", size=16, weight=ft.FontWeight.BOLD, color="#BB6F19"),
            ft.Container(
                content=edit_photo_preview,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=5,
                alignment=ft.alignment.center,
                width=110,
                height=110
            ),
            ft.ElevatedButton(
                "Upload Photo",
                icon=ft.Icons.UPLOAD,
                on_click=edit_upload_photo,
                style=ft.ButtonStyle(
                    bgcolor="#BB6F19",
                    color=ft.Colors.WHITE,
                    padding=ft.padding.symmetric(horizontal=20, vertical=10)
                )
            ),
            ft.Container(
                content=edit_photo_upload_status,
                padding=ft.padding.symmetric(vertical=5),
                alignment=ft.alignment.center
            ),
        ],
        expand=True,
    )

    # Update the add product modal to use the new photo upload section
    add_product_modal = ft.Container(
        visible=False,
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
        expand=True,
        content=ft.Container(
            width=700,
            height=500,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            padding=ft.padding.all(30),
            alignment=ft.alignment.center,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                controls=[
                    # Header Section with Button and Close
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                # Close button positioned absolutely
                                ft.Container(
                                    content=ft.ElevatedButton(
                                        text="X",
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_300,
                                            color=ft.Colors.BLACK,
                                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                            shape=ft.RoundedRectangleBorder(radius=5),
                                        ),
                                        on_click=close_add_product_dialog,
                                    ),
                                    alignment=ft.alignment.top_left,
                                ),
                                # Centered header content
                                ft.Container(
                                    content=ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=5,
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.ADD_CIRCLE,
                                                size=40,
                                                color="#BB6F19"
                                            ),
                                            ft.Text(
                                                "Add Product",
                                                size=24,
                                                weight=ft.FontWeight.BOLD,
                                                color="#BB6F19",
                                            ),
                                            ft.Text(
                                                "Create new product information below",
                                                size=12,
                                                color=ft.Colors.GREY,
                                            ),
                                        ],
                                    ),
                                    alignment=ft.alignment.center,
                                    width=700,
                                ),
                            ],
                        ),
                        padding=ft.padding.only(bottom=10),
                    ),
                    # Form Fields Section with Two Columns
                    ft.Container(
                        content=ft.Row(
                            spacing=20,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                # Left Column: Product Details
                                ft.Column(
                                    spacing=15,
                                    controls=[
                                        ft.Text("Product Details", size=16, weight=ft.FontWeight.BOLD, color="#BB6F19"),
                                        add_name_field,
                                        add_type_price_row,
                                        add_availability_dropdown,
                                        # Buttons Section
                                        ft.Row(
                                            controls=[
                                                ft.ElevatedButton(
                                                    "Add Product",
                                                    style=ft.ButtonStyle(
                                                        color=ft.Colors.WHITE,
                                                        bgcolor="#BB6F19",
                                                        padding=ft.padding.symmetric(horizontal=24, vertical=12),
                                                        shape=ft.RoundedRectangleBorder(radius=8),
                                                    ),
                                                    width=160,
                                                    on_click=save_product
                                                ),
                                                ft.OutlinedButton(
                                                    "Cancel",
                                                    style=ft.ButtonStyle(
                                                        padding=ft.padding.symmetric(horizontal=24, vertical=12),
                                                    ),
                                                    width=160,
                                                    on_click=close_add_product_dialog
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.END,
                                            spacing=10,
                                        ),
                                    ],
                                    expand=True,
                                ),
                                # Right Column: Photo Upload and Preview
                                add_photo_upload_section,
                            ],
                        ),
                        width=650,
                    ),
                    # Messages Section
                    ft.Container(
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0,
                            controls=[
                                error_text,
                                success_text,
                            ],
                        ),
                        padding=ft.padding.symmetric(vertical=2),
                    ),
                ],
            ),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
        )
    )

    # Create a modal for displaying messages
    message_modal_title = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color="#BB6F19")
    message_modal_content = ft.Text("", size=14, color=ft.Colors.GREY)
    message_modal = ft.Container(
        visible=False,
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
        expand=True,
        content=ft.Container(
            width=400,
            height=200,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            padding=ft.padding.all(20),
            alignment=ft.alignment.center,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                controls=[
                    message_modal_title,
                    message_modal_content,
                    ft.ElevatedButton(
                        "OK",
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor="#BB6F19",
                            padding=ft.padding.symmetric(horizontal=20, vertical=10),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=lambda e: close_message_dialog(),
                    ),
                ],
            ),
        ),
    )

    def show_message_dialog(title, message):
        # Update the modal content
        message_modal_title.value = title
        message_modal_content.value = message
        message_modal.visible = True
        page.update()

    def close_message_dialog():
        message_modal.visible = False
        page.update()

    # Fetch products from the database
    def fetch_products():
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("SELECT product_id, name, type, price, availability FROM products ORDER BY product_id")
                products = cursor.fetchall()
                cursor.close()
                conn.close()
                return products
            else:
                print("Error: Unable to connect to the database.")  # Debugging: Connection failure
                show_message_dialog("Error", "Unable to connect to the database.")
                return []
        except Exception as e:
            print(f"Error fetching products: {str(e)}")  # Debugging: Exception details
            show_message_dialog("Error", f"Unable to fetch products: {str(e)}")
            return []

    # Initialize products list and filtered products
    products = fetch_products()
    filtered_products = products.copy()  # Start with all products
    current_filter = "All"  # Track current filter type
    search_query = ""  # Track current search query

    def filter_and_search():
        nonlocal filtered_products
        # First apply type filter
        if current_filter == "All":
            temp_products = products.copy()
        else:
            temp_products = [p for p in products if p[2].lower() == current_filter.lower()]
        
        # Then apply search filter if there's a search query
        if search_query:
            search_lower = search_query.lower()
            filtered_products = [
                p for p in temp_products 
                if search_lower in p[0].lower() or  # Search in product ID
                   search_lower in p[1].lower() or  # Search in product name
                   search_lower in p[2].lower()     # Search in product type
            ]
        else:
            filtered_products = temp_products
        
        refresh_filtered_table()

    def filter_products(product_type):
        nonlocal current_filter, filter_buttons
        current_filter = product_type
        # Update all buttons' styles dynamically
        filter_buttons.controls = [
            create_filter_button(label, category)
            for label, category in zip(CATEGORIES, CATEGORIES)
        ]
        filter_and_search()
        page.update()

    def handle_search(e):
        nonlocal search_query
        search_query = e.control.value
        filter_and_search()

    # Create search field
    search_field = ft.TextField(
        hint_text="Search products...",
        width=300,
        height=40,
        border=ft.InputBorder.OUTLINE,
        filled=True,
        bgcolor=ft.Colors.WHITE,
        prefix_icon=ft.Icons.SEARCH,
        border_radius=15, 
        on_change=handle_search
    )

    # Create filter buttons
    def create_filter_button(label, category):
        is_selected = current_filter == category
        return ft.ElevatedButton(
            label,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE if is_selected else "#BB6F19",
                bgcolor="#BB6F19" if is_selected else "#F5E9DA",  # Active state for clicked category
                side=ft.border.all(1, ft.Colors.BLACK),  # Updated border color to black
                padding=ft.padding.symmetric(horizontal=15, vertical=8),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=lambda e: filter_products(category)
        )

    def filter_products(product_type):
        nonlocal current_filter, filter_buttons
        current_filter = product_type
        # Update all buttons' styles dynamically
        filter_buttons.controls = [
            create_filter_button(label, category)
            for label, category in zip(CATEGORIES, CATEGORIES)
        ]
        filter_and_search()
        page.update()

    # Create filter buttons
    filter_buttons = ft.Row(
        controls=[
            create_filter_button("All", "All"),
            create_filter_button("Milk Tea", "Milk Tea"),
            create_filter_button("Iced Coffee", "Iced Coffee"),
            create_filter_button("Fruit Tea", "Fruit Tea"),
            create_filter_button("Hot Brew", "Hot Brew"),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START
    )

    # Create a container for the product table
    table_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Products", size=24, weight="bold", color="#BB6F19"),
                    ft.Row([
                        filter_buttons,  # Filter buttons
                        ft.Container(width=270),  # Add spacing to push search bar to the right
                        ft.Container(
                            content=search_field,  # Search field
                            margin=ft.margin.only(left=20)
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                "Add Product",
                                icon=ft.Icons.ADD,
                                on_click=show_add_product_form,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor="#BB6F19",
                                    padding=ft.padding.symmetric(horizontal=20, vertical=10)
                                )
                            ),
                            margin=ft.margin.only(left=20)
                        ),
                    ], alignment=ft.MainAxisAlignment.START, spacing=10),  # Align all elements together
                ], spacing=10),
            ], alignment="spaceBetween", spacing=10),
            ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Product ID", weight="bold")),
                                ft.DataColumn(ft.Text("Product Name", weight="bold")),
                                ft.DataColumn(ft.Text("Type", weight="bold")),
                                ft.DataColumn(ft.Text("Price", weight="bold")),
                                ft.DataColumn(ft.Text("Status", weight="bold")),
                                ft.DataColumn(ft.Text("Actions", weight="bold")),
                            ],
                            rows=[
                                ft.DataRow(
                                    cells=[
                                        ft.DataCell(ft.Text(product[0])),
                                        ft.DataCell(ft.Text(product[1])),
                                        ft.DataCell(ft.Text(product[2])),
                                        ft.DataCell(ft.Text(f"₱{product[3]:.2f}")),
                                        ft.DataCell(
                                            ft.Container(
                                                content=ft.Text(product[4], weight="bold"),
                                                bgcolor=(
                                                    "#DFF2BF" if product[4] == "Available" else
                                                    "#FFE6CC" if product[4] == "Limited" else
                                                    "#E0E0E0"
                                                ),
                                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                                border_radius=5
                                            )
                                        ),
                                        ft.DataCell(
                                            ft.Row([
                                                ft.IconButton(
                                                    icon=ft.Icons.EDIT,
                                                    icon_color=ft.Colors.BLUE,
                                                    tooltip="Edit",
                                                    on_click=lambda e, pid=product[0]: show_edit_product_form(pid)
                                                ),
                                                ft.IconButton(
                                                    icon=ft.Icons.DELETE,
                                                    icon_color=ft.Colors.RED,
                                                    tooltip="Delete",
                                                    on_click=lambda e, pid=product[0], pname=product[1]: delete_product(pid, pname)
                                                )
                                            ])
                                        )
                                    ]
                                ) for product in filtered_products
                            ]
                        )
                    ],
                    expand=True,
                ),
                height=550,
                width=1300,
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                padding=10,
            ),
        ], spacing=20),
        expand=True
    )

    def refresh_table():
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("SELECT product_id, name, type, price, availability FROM products ORDER BY product_id")
                fetched_products = cursor.fetchall()
                cursor.close()
                conn.close()

                # Update both products and filtered_products
                nonlocal products, filtered_products
                products = fetched_products
                # Reapply current filter and search
                filter_and_search()
        except Exception as e:
            print(f"Error refreshing table: {str(e)}")
            show_message_dialog("Error", f"Unable to refresh table: {str(e)}")

    def delete_product(product_id, product_name):
        # Show confirmation dialog before deleting
        def confirm_delete(e):
            try:
                conn = get_db_connection()
                if conn and conn.is_connected():
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    refresh_table()  # Refresh the table after deletion
                    show_message_dialog("Success", f"Product '{product_name}' deleted successfully!")
            except Exception as ex:
                show_message_dialog("Error", "An error occurred while deleting the product.")
                print(f"Error deleting product: {str(ex)}")
            finally:
                delete_product_modal.visible = False
                page.update()

        # Create a modal for delete confirmation
        delete_product_modal = ft.Container(
            visible=True,
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
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        ft.Text(
                            f"Are you sure you want to delete the product '{product_name}' (ID: {product_id})?",
                            size=14,
                            color=ft.Colors.GREY,
                            text_align="center"
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20,
                            controls=[
                                ft.ElevatedButton(
                                    "Cancel",
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.GREY,
                                        color=ft.Colors.WHITE,
                                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    on_click=lambda e: close_delete_modal(),
                                ),
                                ft.ElevatedButton(
                                    "Delete",
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.RED,
                                        color=ft.Colors.WHITE,
                                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    on_click=confirm_delete,
                                ),
                            ]
                        )
                    ]
                )
            )
        )

        def close_delete_modal():
            delete_product_modal.visible = False
            page.update()

        # Add the modal to the page
        page.overlay.append(delete_product_modal)
        page.update()

    # Ensure the modal is added to the page overlay during initialization
    if add_product_modal not in page.overlay:
        page.overlay.append(add_product_modal)

    def show_edit_product_form(product_id):
        nonlocal product_id_to_edit
        product_id_to_edit = product_id

        # Fetch product details from the database
        conn = get_db_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT name, type, price, availability, image_path FROM products WHERE product_id = %s", (product_id,))
            product = cursor.fetchone()
            cursor.close()
            conn.close()

            if product:
                # Pre-fill the edit form fields with the product's data
                edit_name_field.value = product[0]  # Name
                edit_type_dropdown.value = product[1]  # Type
                edit_price_field.value = str(product[2])  # Price
                edit_availability_dropdown.value = product[3]  # Availability
                
                # Handle the photo
                nonlocal edit_uploaded_photo_path
                edit_uploaded_photo_path = product[4]  # Set the uploaded photo path
                if edit_uploaded_photo_path:
                    try:
                        # Get absolute path for the image
                        abs_image_path = os.path.abspath(edit_uploaded_photo_path)
                        if os.path.exists(abs_image_path):
                            # Display the uploaded photo in the preview
                            edit_photo_preview.content = ft.Image(
                                src=abs_image_path,
                                width=100,
                                height=100,
                                fit=ft.ImageFit.COVER,
                                border_radius=8,
                                repeat=ft.ImageRepeat.NO_REPEAT,
                                gapless_playback=True
                            )
                            # Update the photo upload status
                            edit_photo_upload_status.value = f"Current image: {os.path.basename(edit_uploaded_photo_path)}"
                            edit_photo_upload_status.color = ft.Colors.GREY
                        else:
                            # If image file doesn't exist, show error
                            edit_photo_preview.content = None
                            edit_photo_upload_status.value = "Image file not found"
                            edit_photo_upload_status.color = ft.Colors.RED
                    except Exception as e:
                        print(f"Error loading image: {str(e)}")
                        edit_photo_preview.content = None
                        edit_photo_upload_status.value = "Error loading image"
                        edit_photo_upload_status.color = ft.Colors.RED
                else:
                    # No image available
                    edit_photo_preview.content = None
                    edit_photo_upload_status.value = "No image available"
                    edit_photo_upload_status.color = ft.Colors.GREY

                edit_photo_upload_status.visible = True
                edit_photo_preview.visible = True
                
                # Show the edit product modal
                edit_product_modal.visible = True
                page.update()
            else:
                show_message_dialog("Error", "Product not found")

    def save_edited_product(e):
        nonlocal product_id_to_edit

        # Validate required fields
        if not all([edit_name_field.value, edit_type_dropdown.value, edit_price_field.value, edit_availability_dropdown.value]):
            error_text.value = "Please fill in all fields."
            success_text.value = ""
            page.update()
            return

        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()

                # Check if the type has changed
                cursor.execute("SELECT type FROM products WHERE product_id = %s", (product_id_to_edit,))
                current_type = cursor.fetchone()[0]
                new_type = edit_type_dropdown.value

                # Update product ID if the type has changed
                if current_type != new_type:
                    type_prefix = {
                        "Milk Tea": "MT",
                        "Iced Coffee": "IC",
                        "Fruit Tea": "FT",
                        "Hot Brew": "HB"
                    }.get(new_type, "OT")  # Default to "OT" for other types

                    cursor.execute(
                        f"SELECT MAX(CAST(SUBSTRING(product_id, 4) AS UNSIGNED)) FROM products WHERE product_id LIKE '{type_prefix}-%'"
                    )
                    max_id = cursor.fetchone()[0]
                    next_id = (max_id + 1) if max_id else 1
                    new_product_id = f"{type_prefix}-{next_id:03d}"

                    # Update the product ID
                    cursor.execute(
                        """
                        UPDATE products
                        SET product_id = %s
                        WHERE product_id = %s
                        """,
                        (new_product_id, product_id_to_edit)
                    )
                    product_id_to_edit = new_product_id  # Update the variable

                # Update the product details
                cursor.execute(
                    """
                    UPDATE products
                    SET name = %s, type = %s, price = %s, availability = %s, image_path = %s
                    WHERE product_id = %s
                    """,
                    (
                        edit_name_field.value,
                        new_type,
                        float(edit_price_field.value),
                        edit_availability_dropdown.value,
                        edit_uploaded_photo_path,
                        product_id_to_edit
                    )
                )
                conn.commit()
                cursor.close()
                conn.close()

                # Create success message container
                success_container = ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,  # Adjusted spacing for better layout
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE,
                                size=60,  # Increased icon size for better visibility
                                color=ft.Colors.GREEN
                            ),
                            ft.Text(
                                "Product Updated Successfully!",
                                size=22,  # Increased text size for emphasis
                                weight=ft.FontWeight.BOLD,
                                color="#BB6F19",
                                text_align=ft.TextAlign.CENTER  # Centered text alignment
                            ),
                            ft.Text(
                                "Your product details have been updated.",
                                size=14,
                                color=ft.Colors.GREY,
                                text_align=ft.TextAlign.CENTER  # Centered text alignment
                            ),
                            ft.ElevatedButton(
                                "OK",
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor="#BB6F19",
                                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                                on_click=lambda e: close_success_and_edit_form()
                            )
                        ]
                    ),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,  # Increased border radius for rounded corners
                    width=350,  # Adjusted width for better layout
                    height=300,  # Adjusted height for better layout
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                        offset=ft.Offset(0, 3)
                    )
                )

                # Create success modal
                success_modal = ft.Container(
                    visible=True,
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                    expand=True,
                    content=success_container
                )

                def close_success_and_edit_form():
                    success_modal.visible = False
                    edit_product_modal.visible = False
                    # Remove success modal from overlay
                    if success_modal in page.overlay:
                        page.overlay.remove(success_modal)
                    page.update()
                    refresh_table()

                # Add success modal to page overlay
                page.overlay.append(success_modal)
                page.update()

            else:
                error_text.value = "Unable to connect to the database."
                success_text.value = ""
                page.update()
        except ValueError as ve:
            error_text.value = "Please enter a valid price."
            success_text.value = ""
            page.update()
            print(f"Value error: {str(ve)}")
        except Exception as e:
            error_text.value = "An error occurred while updating the product."
            success_text.value = ""
            page.update()
            print(f"Error updating product: {str(e)}")

    def close_edit_product_dialog(e=None):
        # Don't clear fields when closing edit modal, just hide it
        edit_product_modal.visible = False
        page.update()

    # Create a modal for editing products
    edit_product_modal = ft.Container(
        visible=False,
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
        expand=True,
        content=ft.Container(
            width=700,
            height=500,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            padding=ft.padding.all(30),
            alignment=ft.alignment.center,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                controls=[
                    # Header Section with Button and Close
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                # Close button positioned absolutely
                                ft.Container(
                                    content=ft.ElevatedButton(
                                        text="X",
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_300,
                                            color=ft.Colors.BLACK,
                                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                            shape=ft.RoundedRectangleBorder(radius=5),
                                        ),
                                        on_click=close_edit_product_dialog,
                                    ),
                                    alignment=ft.alignment.top_left,
                                ),
                                # Centered header content
                                ft.Container(
                                    content=ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=5,
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.EDIT,
                                                size=40,
                                                color="#BB6F19"
                                            ),
                                            ft.Text(
                                                "Edit Product",
                                                size=24,
                                                weight=ft.FontWeight.BOLD,
                                                color="#BB6F19",
                                            ),
                                            ft.Text(
                                                "Update product information below",
                                                size=12,
                                                color=ft.Colors.GREY,
                                            ),
                                        ],
                                    ),
                                    alignment=ft.alignment.center,
                                    width=700,
                                ),
                            ],
                        ),
                        padding=ft.padding.only(bottom=10),
                    ),
                    # Form Fields Section with Two Columns
                    ft.Container(
                        content=ft.Row(
                            spacing=20,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                # Left Column: Product Details
                                ft.Column(
                                    spacing=15,
                                    controls=[
                                        ft.Text("Product Details", size=16, weight=ft.FontWeight.BOLD, color="#BB6F19"),
                                        edit_name_field,
                                        edit_type_price_row,
                                        edit_availability_dropdown,
                                        # Buttons Section
                                        ft.Row(
                                            controls=[
                                                ft.ElevatedButton(
                                                    "Save Changes",
                                                    style=ft.ButtonStyle(
                                                        color=ft.Colors.WHITE,
                                                        bgcolor="#BB6F19",
                                                        padding=ft.padding.symmetric(horizontal=24, vertical=12),
                                                        shape=ft.RoundedRectangleBorder(radius=8),
                                                    ),
                                                    width=160,
                                                    on_click=save_edited_product
                                                ),
                                                ft.OutlinedButton(
                                                    "Cancel",
                                                    style=ft.ButtonStyle(
                                                        padding=ft.padding.symmetric(horizontal=24, vertical=12),
                                                    ),
                                                    width=160,
                                                    on_click=close_edit_product_dialog
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.END,
                                            spacing=10,
                                        ),
                                    ],
                                    expand=True,
                                ),
                                # Right Column: Photo Upload and Preview
                                edit_photo_upload_section,
                            ],
                        ),
                        width=650,
                    ),
                    # Messages Section
                    ft.Container(
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=0,
                            controls=[
                                error_text,
                                success_text,
                            ],
                        ),
                        padding=ft.padding.symmetric(vertical=2),
                    ),
                ],
            ),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
        )
    )

    # Ensure the edit modal is added to the page overlay during initialization
    if edit_product_modal not in page.overlay:
        page.overlay.append(edit_product_modal)

    def refresh_filtered_table():
        # Update the DataTable rows with the filtered products
        if table_container.content and len(table_container.content.controls) > 1:
            list_view = table_container.content.controls[1].content
            if list_view and len(list_view.controls) > 0 and isinstance(list_view.controls[0], ft.DataTable):
                data_table = list_view.controls[0]
                data_table.rows = [
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(product[0])),  # Product ID
                            ft.DataCell(ft.Text(product[1])),  # Product Name
                            ft.DataCell(ft.Text(product[2])),  # Type
                            ft.DataCell(ft.Text(f"₱{product[3]:.2f}")),  # Price
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(product[4], weight="bold"),
                                    bgcolor=(
                                        "#DFF2BF" if product[4] == "Available" else
                                        "#FFE6CC" if product[4] == "Limited" else
                                        "#E0E0E0"
                                    ),
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=5
                                )
                            ),  # Availability
                            ft.DataCell(
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        icon_color=ft.Colors.BLUE,
                                        tooltip="Edit",
                                        on_click=lambda e, pid=product[0]: show_edit_product_form(pid)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_color=ft.Colors.RED,
                                        tooltip="Delete",
                                        on_click=lambda e, pid=product[0], pname=product[1]: delete_product(pid, pname)
                                    )
                                ])
                            )
                        ]
                    ) for product in filtered_products
                ]
                data_table.update()

    # Get current date and time
    today = datetime.now()
    day_str = today.strftime('%A')
    date_str = today.strftime('%d %B %Y')

    # User profile card
    def user_profile_card():
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

        return ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLACK),
                    bgcolor="#BB6F19",
                    radius=18
                ),
                ft.Column([
                    ft.Text(admin_full_name, weight="bold", size=16, font_family="Poppins"),
                    ft.Text("Barista", size=12, color=ft.Colors.GREY, font_family="Poppins")
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
                                ft.Text("Manage Products", size=24, weight="bold", color="#BB6F19"),
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
                table_container
            ],
            spacing=20
        ),
        padding=20,
        expand=True
    )