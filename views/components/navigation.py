import flet as ft
from views.dashboard import dashboard_view
from views.products import products_view
from views.transactions import transactions_view
from views.reports import reports_view

class Navigation:
    def __init__(self, page: ft.Page, content_container=None):
        self.page = page
        self.content_container = content_container
        self.current_view = "dashboard"
        self.views = {
            "dashboard": dashboard_view,
            "products": products_view,
            "transactions": transactions_view,
            "reports": reports_view
        }
        self.on_tab_change = None

    def sidebar(self):
        return ft.Container(
            width=220,
            bgcolor=ft.Colors.WHITE,
            content=ft.Column([
                ft.Row([
                    ft.Image(src="logos/bigbrew_logo_brown.png", width=40, height=40),
                    ft.Text(
                        "BIGBREW",
                        weight="bold",
                        size=25,
                        color="#BB6F19",
                        font_family="Poppins"
                    )
                ], spacing=10, alignment="center"),
                ft.Divider(),
                self._nav_item("dashboard", "Dashboard", ft.Icons.DASHBOARD),
                self._nav_item("products", "Manage Product", ft.Icons.INVENTORY_2_OUTLINED),
                self._nav_item("transactions", "Transactions", ft.Icons.RECEIPT_LONG_OUTLINED),
                self._nav_item("reports", "Sales Reports", ft.Icons.BAR_CHART),
            ], spacing=20, alignment="start"),
            padding=20,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
        )

    def _nav_item(self, view_name: str, label: str, icon: str):
        is_active = self.current_view == view_name
        container = ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=ft.Colors.BLACK),
                ft.Text(
                    label,
                    weight="bold" if is_active else None,
                    color="#BB6F19",
                    font_family="Poppins"
                )
            ], spacing=10),
            on_click=lambda e: self._change_view(view_name),
            padding=10,
            border_radius=5,
            bgcolor=ft.Colors.AMBER_50 if is_active else None
        )

        # Add hover effect
        def on_hover(e):
            container.bgcolor = ft.Colors.AMBER_100 if e.data == "true" and not is_active else (ft.Colors.AMBER_50 if is_active else None)
            container.update()

        container.on_hover = on_hover
        return container

    def _change_view(self, view_name: str):
        if self.on_tab_change:
            self.on_tab_change(view_name)
        else:
            self.current_view = view_name
            if self.content_container:
                self.content_container.content = self.views[self.current_view](self.page)
                self.content_container.update()
                self.page.update()

    def get_current_view(self):
        return self.views[self.current_view](self.page)