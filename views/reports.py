import flet as ft
from config.database import get_db_connection, get_employee_full_name
import os
import datetime

# Cache for storing generated charts
chart_cache = {}

class ReportState:
    def __init__(self):
        self.filter = "today"  # Default timeline set to "today"

state = ReportState()

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

def get_products_ordered_by_hour(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    results = []
    for hour in range(13, 20):  # 1PM (13) to 7PM (19)
        start = datetime.datetime.combine(date, datetime.time(hour, 0, 0))
        end = start + datetime.timedelta(hours=1)
        cursor.execute(
            """
            SELECT COALESCE(SUM(quantity), 0)
            FROM orders
            WHERE created_at >= %s AND created_at < %s
            """,
            (start, end)
        )
        count = cursor.fetchone()[0]
        results.append(count)
    cursor.close()
    conn.close()
    return results

def get_products_ordered_by_day(start_date, days):
    conn = get_db_connection()
    cursor = conn.cursor()
    results = []
    for i in range(days):
        day = start_date + datetime.timedelta(days=i)
        start = datetime.datetime.combine(day, datetime.time(0, 0, 0))
        end = start + datetime.timedelta(days=1)
        cursor.execute(
            """
            SELECT COALESCE(SUM(quantity), 0)
            FROM orders
            WHERE created_at >= %s AND created_at < %s
            """,
            (start, end)
        )
        count = cursor.fetchone()[0]
        results.append(count)
    cursor.close()
    conn.close()
    return results

def get_product_type_statistics():
    conn = get_db_connection()
    if conn and conn.is_connected():
        cursor = conn.cursor()
        try:
            # Get the sum of quantities for each product type from orders
            cursor.execute("""
                SELECT p.type, COALESCE(SUM(o.quantity), 0) as total_quantity
                FROM products p
                LEFT JOIN orders o ON p.name = o.product_name
                WHERE o.status != 'Pending'
                GROUP BY p.type
                ORDER BY total_quantity DESC
            """)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error getting product statistics: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    return []

def build_line_and_bar_charts(page, filter_type):
    max_x_val = 6  # Default fallback
    if filter_type == "today":
        today_date = datetime.date.today()
        yesterday_date = today_date - datetime.timedelta(days=1)
        hours = ["1PM", "2PM", "3PM", "4PM", "5PM", "6PM", "7PM"]
        today = get_products_ordered_by_hour(today_date)
        yesterday = get_products_ordered_by_hour(yesterday_date)
        x_labels = hours
        x_label_objs = [
            ft.ChartAxisLabel(value=i, label=ft.Text(hours[i], size=14, weight=ft.FontWeight.BOLD)) for i in range(len(hours))
        ]
        bar_x_labels = x_labels
        bar_x_label_objs = x_label_objs
        max_x_val = len(hours) - 1
    elif filter_type == "week":
        today_date = datetime.date.today()
        start_date = today_date - datetime.timedelta(days=6)
        days = [(start_date + datetime.timedelta(days=i)).strftime("%a") for i in range(7)]
        this_week = get_products_ordered_by_day(start_date, 7)
        last_week_start = start_date - datetime.timedelta(days=7)
        last_week = get_products_ordered_by_day(last_week_start, 7)
        today = this_week
        yesterday = last_week
        x_labels = days
        x_label_objs = [
            ft.ChartAxisLabel(value=i, label=ft.Text(days[i], size=14, weight=ft.FontWeight.BOLD)) for i in range(len(days))
        ]
        bar_x_labels = x_labels
        bar_x_label_objs = x_label_objs
        max_x_val = len(days) - 1
    elif filter_type == "month":
        today_date = datetime.date.today()
        start_date = today_date.replace(day=1)
        days_in_month = (today_date.replace(month=today_date.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day
        # Get per-day data for this and last month
        this_month = get_products_ordered_by_day(start_date, days_in_month)
        prev_month_last_day = start_date - datetime.timedelta(days=1)
        prev_month_start = prev_month_last_day.replace(day=1)
        prev_month_days = prev_month_last_day.day
        last_month = get_products_ordered_by_day(prev_month_start, prev_month_days)
        # Group into 4 buckets: 1-7, 8-14, 15-21, 22-28 (always 4 buckets)
        def group_weekly(data):
            buckets = []
            for i in range(0, 28, 7):  # Always 4 buckets for 28 days
                if i < len(data):
                    buckets.append(sum(data[i:i+7]))
                else:
                    buckets.append(0)
            while len(buckets) < 4:
                buckets.append(0)
            return buckets[:4]
        today = group_weekly(this_month)
        yesterday = group_weekly(last_month)
        x_labels = ["WK1", "WK2", "WK3", "WK4"]
        x_label_objs = [
            ft.ChartAxisLabel(value=i, label=ft.Text(x_labels[i], size=14, weight=ft.FontWeight.BOLD)) for i in range(4)
        ]
        bar_x_labels = x_labels
        bar_x_label_objs = [
            ft.ChartAxisLabel(value=i, label=ft.Text(x_labels[i], size=14, weight=ft.FontWeight.BOLD)) for i in range(4)
        ]
        max_x_val = 3
    else:
        today = yesterday = x_labels = x_label_objs = bar_x_labels = bar_x_label_objs = []

    today_data = [ft.LineChartDataPoint(x, y) for x, y in enumerate(today)]
    yesterday_data = [ft.LineChartDataPoint(x, y) for x, y in enumerate(yesterday)]
    bar_chart = ft.Container(
        bgcolor="white",
        border_radius=16,
        padding=20,
        width=1000,
        content=ft.Column([
            ft.Text("Sales by Hour of the Day", size=16, color="#BB6F19", weight="bold"),
            ft.Row([
                ft.Row([
                    ft.Container(width=16, height=8, bgcolor="#BB6F19", border_radius=4),
                    ft.Text("Today", size=14, weight=ft.FontWeight.BOLD),
                ], spacing=8),
                ft.Row([
                    ft.Container(width=16, height=8, bgcolor="#D4A76A", border_radius=4),
                    ft.Text("Yesterday", size=14, weight=ft.FontWeight.BOLD),
                ], spacing=8),
            ], spacing=20, alignment="start"),
            ft.LineChart(
                data_series=[
                    ft.LineChartData(
                        data_points=today_data,
                        stroke_width=4,
                        color="#BB6F19",
                        curved=True,
                        stroke_cap_round=True,
                    ),
                    ft.LineChartData(
                        data_points=yesterday_data,
                        stroke_width=4,
                        color="#D4A76A",
                        curved=True,
                        stroke_cap_round=True,
                    ),
                ],
                border=ft.border.all(3, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)),
                horizontal_grid_lines=ft.ChartGridLines(
                    interval=10, color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE), width=1
                ),
                vertical_grid_lines=ft.ChartGridLines(
                    interval=1, color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE), width=1
                ),
                left_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(value=0, label=ft.Text("0", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=10, label=ft.Text("10", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=20, label=ft.Text("20", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=30, label=ft.Text("30", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=40, label=ft.Text("40", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=50, label=ft.Text("50", size=14, weight=ft.FontWeight.BOLD)),
                    ],
                    labels_size=40,
                ),
                bottom_axis=ft.ChartAxis(
                    labels=x_label_objs,
                    labels_size=32,
                ),
                tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
                min_y=0,
                max_y=50,
                min_x=0,
                max_x=max_x_val if today else 6,
                width=1000,
                height=300,
                expand=True,
            ),
        ], spacing=10),
        height=350,
    )

    bar_groups = [
        ft.BarChartGroup(
            x=i,
            bar_rods=[
                ft.BarChartRod(
                    from_y=0,
                    to_y=today[i],
                    width=32,
                    color="#BB6F19",
                    border_radius=0,
                )
            ],
        ) for i in range(len(bar_x_labels))
    ]
    sales_trend_chart = ft.Container(
        bgcolor="white",
        border_radius=16,
        padding=20,
        width=350,
        height=250,
        content=ft.Column([
            ft.Text("Weekly Sales Trend", size=16, color="#BB6F19", weight="bold"),
            ft.BarChart(
                bar_groups=bar_groups,
                groups_space=16,
                border=ft.border.all(1, ft.Colors.GREY_400),
                left_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(value=0, label=ft.Text("0", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=5, label=ft.Text("5", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=10, label=ft.Text("10", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=15, label=ft.Text("15", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=20, label=ft.Text("20", size=14, weight=ft.FontWeight.BOLD)),
                        ft.ChartAxisLabel(value=30, label=ft.Text("30", size=14, weight=ft.FontWeight.BOLD)),
                    ],
                    labels_size=40,
                ),
                bottom_axis=ft.ChartAxis(
                    labels=bar_x_label_objs,
                    labels_size=40,
                ),
                horizontal_grid_lines=ft.ChartGridLines(
                    interval=5, color=ft.Colors.GREY_300, width=1
                ),
                tooltip_bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY_300),
                max_y=30,
                interactive=True,
                width=320,
                height=160,
                expand=True,
            ),
        ], spacing=10),
    )
    return bar_chart, sales_trend_chart

def filter_button(label, filter_type, selected, on_click):
    return ft.ElevatedButton(
        label,
        style=ft.ButtonStyle(
            bgcolor="#BB6F19" if selected else "#FFFFFF",  # Brown when selected, white otherwise
            color="white" if selected else "#BB6F19",  # Text color changes based on selection
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(2, "#BB6F19"),  # Add border
        ),
        on_click=lambda e: on_click(filter_type),
        disabled=False,
    )

def reports_view(page: ft.Page):
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
                    ft.Text("Sales Report", size=24, weight="bold", color="#BB6F19"),
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
                                ft.Text("Barista", size=12, color="grey", font_family="Poppins")
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

    # --- CHARTS ---
    # Get real data from database
    product_stats = get_product_type_statistics()
    categories = [stat[0] for stat in product_stats]  # Product types
    values = [stat[1] for stat in product_stats]      # Quantities
    colors = ['#BB6F19', '#F5E9DA', '#D4A76A', '#8B4513', '#D2691E', '#CD853F']  # Added more colors for variety

    # Initialize charts with the default timeline
    bar_chart, sales_trend_chart = build_line_and_bar_charts(page, state.filter)
    
    def update_donut_chart(filter_type):
        # Fetch data dynamically based on the filter type
        if filter_type == "today":
            start_date = datetime.date.today()
            end_date = start_date + datetime.timedelta(days=1)
        elif filter_type == "week":
            start_date = datetime.date.today() - datetime.timedelta(days=6)
            end_date = datetime.date.today() + datetime.timedelta(days=1)
        elif filter_type == "month":
            start_date = datetime.date.today().replace(day=1)
            end_date = (start_date.replace(month=start_date.month % 12 + 1, day=1) - datetime.timedelta(days=1)).replace(day=start_date.day)
        else:
            start_date = datetime.date.today()
            end_date = start_date + datetime.timedelta(days=1)

        conn = get_db_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT p.type, COALESCE(SUM(o.quantity), 0) as total_quantity
                    FROM products p
                    LEFT JOIN orders o ON p.name = o.product_name
                    WHERE o.created_at >= %s AND o.created_at < %s AND o.status != 'Pending'
                    GROUP BY p.type
                    ORDER BY total_quantity DESC
                """, (start_date, end_date))
                results = cursor.fetchall()
                categories = [stat[0] for stat in results]
                values = [stat[1] for stat in results]

                # Handle case where there are no orders
                if not values or sum(values) == 0:
                    categories = ["No Orders"]
                    values = [0]

                total = sum(values) if values else 1  # Prevent division by zero
                pie_sections = [
                    ft.PieChartSection(
                        values[i],
                        title=f"{int(values[i] / total * 100)}%" if total > 0 else "0%",
                        title_style=normal_title_style,
                        color=colors[i % len(colors)],
                        radius=normal_radius,
                    ) for i in range(len(categories))
                ]
                legends.controls = [
                    create_legend_item(colors[i % len(colors)], categories[i], values[i]) for i in range(len(categories))
                ]
                chart.sections = pie_sections
                chart.update()
            except Exception as e:
                print(f"Error updating donut chart: {e}")
            finally:
                cursor.close()
                conn.close()
                
    update_donut_chart(state.filter)  # Ensure the donut chart is initialized with "today"

    # --- LEGENDS ---
    def create_legend_item(color, label, value):
        return ft.Row(
            controls=[
                ft.Container(width=16, height=8, bgcolor=color, border_radius=4),
                ft.Text(label, size=12, weight=ft.FontWeight.BOLD),
                ft.Text(f"({value})", size=12, color="grey"),
            ],
            spacing=6,
            alignment="start",
        )

    legends = ft.Column(
        controls=[
            create_legend_item(colors[i % len(colors)], categories[i], values[i]) for i in range(len(categories))
        ],
        spacing=6,
        alignment="start",
    )

    # --- DONUT CHART (Interactive Pie Chart) ---
    normal_radius = 50
    hover_radius = 60
    normal_title_style = ft.TextStyle(
        size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD
    )
    hover_title_style = ft.TextStyle(
        size=22,
        color=ft.Colors.WHITE,
        weight=ft.FontWeight.BOLD,
        shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK54),
    )
    # Calculate percentages for the pie chart
    total = sum(values) if values else 1  # Prevent division by zero
    pie_sections = [
        ft.PieChartSection(
            values[i],
            title=f"{int(values[i] / total * 100)}%" if total > 0 else "0%",
            title_style=normal_title_style,
            color=colors[i % len(colors)],  # Cycle through colors if more categories than colors
            radius=normal_radius,
        ) for i in range(len(categories))
    ]
    def on_chart_event(e: ft.PieChartEvent):
        for idx, section in enumerate(chart.sections):
            if idx == e.section_index:
                section.radius = hover_radius
                section.title_style = hover_title_style
            else:
                section.radius = normal_radius
                section.title_style = normal_title_style
        chart.update()
    chart = ft.PieChart(
        sections=pie_sections,
        sections_space=0,
        center_space_radius=40,
        on_chart_event=on_chart_event,
        expand=True,
    )
    donut_chart = ft.Container(
        bgcolor="white",
        border_radius=16,
        padding=20,
        width=350,
        height=250,
        content=ft.Row([
            ft.Column(
                controls=[
                    ft.Text("Revenue by Category", size=16, color="#BB6F19", weight="bold"),
                    chart,
                ],
                spacing=10,
                expand=True,
            ),
            legends,  # Added legends to the right side of the donut chart
        ], spacing=10),
    )
    
    # --- FILTER CONTROLS ---
    def update_charts(filter_type):
        state.filter = filter_type  # Update the filter state
        bar_chart, sales_trend_chart = build_line_and_bar_charts(page, filter_type)
        update_donut_chart(filter_type)  # Update the donut chart dynamically
        filter_toggle_row.controls = [
            filter_button("Today", "today", state.filter == "today", update_charts),
            filter_button("Week", "week", state.filter == "week", update_charts),
            filter_button("Month", "month", state.filter == "month", update_charts),
        ]  # Re-render buttons with updated state
        right_charts_column.controls[0] = bar_chart
        right_charts_column.controls[1] = charts_row
        charts_row.controls[0] = sales_trend_chart
        page.update()

    filter_toggle_row = ft.Row(
        controls=[
            filter_button("Today", "today", state.filter == "today", update_charts),
            filter_button("Week", "week", state.filter == "week", update_charts),
            filter_button("Month", "month", state.filter == "month", update_charts),
        ],
        spacing=10,
        alignment="start",
    )
    filter_date_row = ft.Row(
        controls=[
            ft.TextField(label="From", value="", width=140, prefix_icon=ft.Icons.CALENDAR_MONTH, border=ft.InputBorder.OUTLINE, filled=True, bgcolor="white"),
            ft.TextField(label="To", value="", width=140, prefix_icon=ft.Icons.CALENDAR_MONTH, border=ft.InputBorder.OUTLINE, filled=True, bgcolor="white"),
            ft.ElevatedButton("Apply", style=ft.ButtonStyle(bgcolor="#BB6F19", color="white", shape=ft.RoundedRectangleBorder(radius=8))),
        ],
        spacing=10,
        alignment="start",
    )
    filter_controls = ft.Column([
        filter_toggle_row,
        ft.Container(filter_date_row, margin=ft.margin.only(top=10)),
    ], spacing=8)

    # --- METRIC CARDS ---
    def metric_card(title, value, change, change_color, subtext, icon, icon_color):
        return ft.Container(
            content=ft.Column([
                # Title row at the top
                ft.Row([
                    ft.CircleAvatar(
                        content=ft.Icon(icon, color=icon_color, size=24),
                        bgcolor=ft.Colors.WHITE,
                        radius=20
                    ),
                    ft.Text(title, weight="bold", size=16, font_family="Poppins"),
                ], spacing=8, alignment="center", vertical_alignment="center"),
                
                # Amount in the center
                ft.Text(value, size=28, weight="bold", font_family="Poppins", text_align="center"),
                
                # Percentage and text at the bottom
                ft.Column([
                    ft.Container(
                        content=ft.Text(change, size=14, color=change_color, weight="bold"),
                        bgcolor=ft.Colors.GREEN_100 if change_color == ft.Colors.GREEN_700 else ft.Colors.RED_100,
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        alignment=ft.alignment.center
                    ),
                    ft.Text(subtext, size=12, color=ft.Colors.GREY_700),
                ], alignment="start", spacing=4),
            ], alignment="center", spacing=2, horizontal_alignment="center"),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            border=ft.border.all(1, ft.Colors.BLACK),
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            expand=True,
            height=150,
            width=380
        )

    def fetch_report_metrics():
        try:
            conn = get_db_connection()
            if conn and conn.is_connected():
                cursor = conn.cursor()

                # Fetch revenue, profit, and total orders for today
                cursor.execute("""
                    SELECT 
                        SUM(price * quantity) AS revenue, 
                        SUM(price * quantity * 0.4) AS profit, 
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
                        SUM(price * quantity) AS revenue, 
                        SUM(price * quantity * 0.4) AS profit, 
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

                cursor.close()
                conn.close()

                return {
                    "revenue_today": revenue_today,
                    "profit_today": profit_today,
                    "total_orders_today": total_orders_today,
                    "revenue_change": revenue_change,
                    "profit_change": profit_change,
                    "total_orders_change": total_orders_change,
                }
        except Exception as e:
            print(f"Error fetching report metrics: {e}")
            return {
                "revenue_today": 0,
                "profit_today": 0,
                "total_orders_today": 0,
                "revenue_change": 0,
                "profit_change": 0,
                "total_orders_change": 0,
            }

    report_metrics = fetch_report_metrics()

    metrics_column = ft.Column(
        controls=[
            metric_card(
                "Total Revenue",
                f"₱{report_metrics['revenue_today']:.2f}",
                f"{'▲' if report_metrics['revenue_change'] >= 0 else '▼'} {abs(report_metrics['revenue_change']):.2f}%",
                ft.Colors.GREEN_700 if report_metrics['revenue_change'] >= 0 else ft.Colors.RED_700,
                "vs yesterday",
                ft.Icons.PAID,
                ft.Colors.GREEN_700
            ),
            metric_card(
                "Total Profit",
                f"₱{report_metrics['profit_today']:.2f}",
                f"{'▲' if report_metrics['profit_change'] >= 0 else '▼'} {abs(report_metrics['profit_change']):.2f}%",
                ft.Colors.GREEN_700 if report_metrics['profit_change'] >= 0 else ft.Colors.RED_700,
                "vs yesterday",
                ft.Icons.ATTACH_MONEY,
                ft.Colors.BLUE_700
            ),
            metric_card(
                "Total Orders",
                f"{report_metrics['total_orders_today']}",
                f"{'▲' if report_metrics['total_orders_change'] >= 0 else '▼'} {abs(report_metrics['total_orders_change']):.2f}%",
                ft.Colors.GREEN_700 if report_metrics['total_orders_change'] >= 0 else ft.Colors.RED_700,
                "vs yesterday",
                ft.Icons.SHOPPING_BAG,
                ft.Colors.ORANGE_700
            ),
        ],
        spacing=20,
        alignment="center"
    )

    # --- CHARTS ---
    charts_row = ft.Row([
        sales_trend_chart,
        donut_chart
    ], spacing=18, alignment="start", vertical_alignment="start")
    right_charts_column = ft.Column([
        bar_chart,
        charts_row
    ], spacing=20, expand=True)

    # --- MAIN CONTENT LAYOUT ---
    main_content = ft.Row([
        ft.Column([
            filter_controls,
            metrics_column
        ], spacing=24, expand=1),
        ft.Container(right_charts_column, expand=2, margin=ft.margin.only(left=28)),
    ], spacing=24, expand=True)

    # User Profile Card
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

    # --- PAGE RETURN ---
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Sales Report", size=24, weight="bold", color="#BB6F19"),
                    ft.Text("Monday, 25 March 2025", size=14, color="black"),
                ], expand=True),
                user_profile_card()
            ], alignment="spaceBetween", vertical_alignment="center"),
            ft.Divider(height=2, thickness=1, color="#BB6F19"),
            ft.Container(main_content, padding=20, expand=True)
        ], spacing=20),
        padding=20,
        expand=True
    )