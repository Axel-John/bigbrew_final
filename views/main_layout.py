import flet as ft
from views.components.navigation import Navigation
from views.dashboard import dashboard_view
from views.products import products_view
from views.transactions import transactions_view
from views.reports import reports_view

def main(page: ft.Page):
    # Page settings
    page.title = "BIGBREW Dashboard"
    page.bgcolor = "#F5E9DA"
    page.padding = 20
    page.fonts = {
        "Poppins": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf",
        "Poppins-Bold": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf",
    }

    # Create containers for sidebar and content
    content_container = ft.Container(expand=True)
    sidebar_container = ft.Container(expand=False)

    def on_tab_change(selected_tab):
        # Update the current view
        navigation.current_view = selected_tab
        
        # Update the sidebar to reflect the new selection
        sidebar_container.content = navigation.sidebar()
        
        # Update the content with the new view
        content_container.content = navigation.get_current_view()
        
        # Update all components
        sidebar_container.update()
        content_container.update()
        page.update()

    # Initialize navigation
    navigation = Navigation(page, content_container=content_container)
    navigation.on_tab_change = on_tab_change
    
    # Set initial view
    sidebar_container.content = navigation.sidebar()
    content_container.content = navigation.get_current_view()

    # Add the layout to the page
    page.add(
        ft.Row([
            sidebar_container,
            ft.VerticalDivider(width=1),
            content_container
        ], expand=True)
    )
    
    # Initial update
    page.update() 