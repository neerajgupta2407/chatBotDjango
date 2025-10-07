"""
Django management command to create dummy data for multi-tenant testing.

Creates:
    - Admin superuser (username: admin, password: admin12345)
    - 5 dummy clients with different configurations
    - 3-4 sessions per client with conversation history
    - Sample file data for testing

Usage:
    python manage.py create_dummy_data [--clean]

Options:
    --clean     Delete existing dummy data before creating new data
"""

import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from chat_sessions.models import Session
from clients.models import Client


class Command(BaseCommand):
    help = "Create dummy data for multi-tenant client testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete existing dummy data before creating new data",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("Creating Multi-Tenant Dummy Data"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

        if options["clean"]:
            self.clean_dummy_data()

        # Create admin user
        self.create_admin_user()

        # Create dummy clients
        clients = self.create_dummy_clients()

        # Create sessions and messages for each client
        for client in clients:
            self.create_sessions_for_client(client)

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("Dummy Data Creation Complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

    def clean_dummy_data(self):
        """Delete existing dummy data."""
        self.stdout.write("\nCleaning existing dummy data...")

        # Delete admin user
        if User.objects.filter(username="admin").exists():
            User.objects.filter(username="admin").delete()
            self.stdout.write(self.style.WARNING(f"  Deleted admin user"))

        # Delete dummy clients (cascade will delete sessions)
        dummy_emails = [
            "contact@techstartup.com",
            "info@ecommerce-store.com",
            "support@healthcare-clinic.com",
            "hello@financecorp.com",
            "admin@realestate-agency.com",
        ]

        deleted_count = Client.objects.filter(email__in=dummy_emails).delete()[0]
        self.stdout.write(
            self.style.WARNING(
                f"  Deleted {deleted_count} dummy client(s) and their sessions"
            )
        )

    def create_admin_user(self):
        """Create admin superuser."""
        self.stdout.write("\n" + self.style.HTTP_INFO("Creating Admin User:"))

        username = "admin"
        email = "admin@admin.com"
        password = "admin12345"

        # Check if admin user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"  ⚠ Admin user already exists: {username}")
            )
            admin_user = User.objects.get(username=username)
            self.stdout.write(f"    Username: {admin_user.username}")
            self.stdout.write(f"    Email: {admin_user.email}")
            return admin_user

        # Create superuser
        admin_user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(self.style.SUCCESS(f"  ✓ Created admin superuser"))
        self.stdout.write(f"    Username: {username}")
        self.stdout.write(f"    Email: {email}")
        self.stdout.write(f"    Password: {password}")
        self.stdout.write(f"    Admin URL: http://localhost:8000/admin/")

        return admin_user

    def create_dummy_clients(self):
        """Create multiple dummy clients with different configurations."""
        self.stdout.write("\n" + self.style.HTTP_INFO("Creating Dummy Clients:"))

        clients_data = [
            {
                "name": "TechStartup Inc",
                "email": "contact@techstartup.com",
                "config": {
                    "bot_name": "TechBot",
                    "primary_color": "#6366f1",
                    "bot_message_bg_color": "#6366f1",
                    "bot_icon_url": "https://api.dicebear.com/7.x/bottts/svg?seed=techbot",
                    "powered_by_text": "Powered by TechStartup",
                    "whitelisted_domains": [
                        "https://techstartup.com",
                        "https://*.techstartup.com",
                        "http://localhost:3000",
                    ],
                    "widget_position": "bottom-right",
                    "widget_size": "medium",
                    "widget_offset": {"x": 20, "y": 20},
                    "initial_state": "minimized",
                    "theme": "light",
                    "enable_file_upload": True,
                    "enable_json_upload": True,
                    "enable_csv_upload": True,
                    "max_file_size_mb": 10,
                },
            },
            {
                "name": "E-Commerce Store",
                "email": "info@ecommerce-store.com",
                "config": {
                    "bot_name": "ShopAssistant",
                    "primary_color": "#10b981",
                    "bot_message_bg_color": "#10b981",
                    "bot_icon_url": "https://api.dicebear.com/7.x/bottts/svg?seed=shopassist",
                    "powered_by_text": "Shopping Helper",
                    "whitelisted_domains": [
                        "https://ecommerce-store.com",
                        "https://*.ecommerce-store.com",
                    ],
                    "widget_position": "bottom-right",
                    "widget_size": "large",
                    "widget_offset": {"x": 30, "y": 30},
                    "initial_state": "open",
                    "theme": "light",
                    "enable_file_upload": True,
                    "enable_json_upload": False,
                    "enable_csv_upload": True,
                    "max_file_size_mb": 5,
                },
            },
            {
                "name": "HealthCare Clinic",
                "email": "support@healthcare-clinic.com",
                "config": {
                    "bot_name": "HealthBot",
                    "primary_color": "#ef4444",
                    "bot_message_bg_color": "#ef4444",
                    "bot_icon_url": "https://api.dicebear.com/7.x/bottts/svg?seed=healthbot",
                    "powered_by_text": "HealthCare Support",
                    "whitelisted_domains": [
                        "https://healthcare-clinic.com",
                    ],
                    "widget_position": "bottom-left",
                    "widget_size": "medium",
                    "widget_offset": {"x": 20, "y": 20},
                    "initial_state": "minimized",
                    "theme": "light",
                    "enable_file_upload": False,
                    "enable_json_upload": False,
                    "enable_csv_upload": False,
                    "max_file_size_mb": 0,
                },
            },
            {
                "name": "Finance Corporation",
                "email": "hello@financecorp.com",
                "config": {
                    "bot_name": "FinanceAI",
                    "primary_color": "#f59e0b",
                    "bot_message_bg_color": "#f59e0b",
                    "bot_icon_url": "https://api.dicebear.com/7.x/bottts/svg?seed=financeai",
                    "powered_by_text": "Finance Corp AI",
                    "whitelisted_domains": ["*"],  # Allow all domains
                    "widget_position": "bottom-right",
                    "widget_size": "small",
                    "widget_offset": {"x": 15, "y": 15},
                    "initial_state": "minimized",
                    "theme": "dark",
                    "enable_file_upload": True,
                    "enable_json_upload": True,
                    "enable_csv_upload": True,
                    "max_file_size_mb": 20,
                },
            },
            {
                "name": "Real Estate Agency",
                "email": "admin@realestate-agency.com",
                "config": {
                    "bot_name": "PropertyBot",
                    "primary_color": "#8b5cf6",
                    "bot_message_bg_color": "#8b5cf6",
                    "bot_icon_url": "https://api.dicebear.com/7.x/bottts/svg?seed=propertybot",
                    "powered_by_text": "Real Estate AI",
                    "whitelisted_domains": [
                        "https://realestate-agency.com",
                        "http://localhost:8000",
                    ],
                    "widget_position": "bottom-right",
                    "widget_size": "medium",
                    "widget_offset": {"x": 20, "y": 20},
                    "initial_state": "minimized",
                    "theme": "auto",
                    "enable_file_upload": True,
                    "enable_json_upload": True,
                    "enable_csv_upload": True,
                    "max_file_size_mb": 15,
                },
            },
        ]

        clients = []
        for data in clients_data:
            client, created = Client.objects.get_or_create(
                email=data["email"],
                defaults={
                    "name": data["name"],
                    "config": data["config"],
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"\n  ✓ Created: {client.name}"))
                self.stdout.write(f"    Email: {client.email}")
                self.stdout.write(f"    API Key: {client.api_key}")
                self.stdout.write(f"    Bot Name: {client.config.get('bot_name')}")
                self.stdout.write(
                    f"    Primary Color: {client.config.get('primary_color')}"
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"\n  ⚠ Already exists: {client.name}")
                )
                self.stdout.write(f"    API Key: {client.api_key}")

            clients.append(client)

        return clients

    def create_sessions_for_client(self, client):
        """Create sessions with messages for a client."""
        self.stdout.write(
            self.style.HTTP_INFO(f"\nCreating Sessions for {client.name}:")
        )

        # Session templates with different scenarios
        session_templates = [
            {
                "config": {
                    "aiProvider": "claude",
                    "pageContext": {
                        "url": "https://example.com/pricing",
                        "title": "Pricing Page",
                    },
                },
                "messages": [
                    {"role": "user", "content": "What are your pricing plans?"},
                    {
                        "role": "assistant",
                        "content": "We offer three pricing plans: Starter ($29/mo), Professional ($79/mo), and Enterprise (custom pricing). Each plan includes different features to match your needs.",
                    },
                    {
                        "role": "user",
                        "content": "What's included in the Professional plan?",
                    },
                    {
                        "role": "assistant",
                        "content": "The Professional plan includes: unlimited users, 50GB storage, priority support, advanced analytics, API access, and custom integrations.",
                    },
                ],
            },
            {
                "config": {
                    "aiProvider": "openai",
                    "pageContext": {
                        "url": "https://example.com/products",
                        "title": "Products",
                    },
                },
                "messages": [
                    {"role": "user", "content": "Tell me about your products"},
                    {
                        "role": "assistant",
                        "content": "We offer a range of innovative products designed to solve modern business challenges. Our flagship products include cloud-based collaboration tools, project management software, and customer relationship management systems.",
                    },
                ],
            },
            {
                "config": {
                    "aiProvider": "claude",
                    "pageContext": {
                        "url": "https://example.com/support",
                        "title": "Support Center",
                    },
                },
                "messages": [
                    {"role": "user", "content": "How can I reset my password?"},
                    {
                        "role": "assistant",
                        "content": "To reset your password: 1) Click 'Forgot Password' on the login page, 2) Enter your email address, 3) Check your email for a reset link, 4) Click the link and create a new password. The link expires in 24 hours.",
                    },
                    {"role": "user", "content": "I didn't receive the email"},
                    {
                        "role": "assistant",
                        "content": "Please check your spam folder first. If you still can't find it, verify you entered the correct email address. You can also contact our support team at support@example.com for immediate assistance.",
                    },
                ],
            },
            {
                "config": {
                    "aiProvider": "claude",
                    "pageContext": {
                        "url": "https://example.com/dashboard",
                        "title": "Dashboard",
                    },
                    "customInstructions": "Be helpful and professional",
                },
                "messages": [
                    {
                        "role": "user",
                        "content": "How do I export my data?",
                    },
                    {
                        "role": "assistant",
                        "content": "You can export your data from the Settings page. Go to Settings > Data Management > Export Data. Choose your preferred format (CSV, JSON, or PDF) and click 'Export'. The file will be prepared and sent to your email within a few minutes.",
                    },
                ],
                "file_data": {
                    "filename": "sample_data.csv",
                    "data": [
                        {"id": 1, "name": "Product A", "price": 99.99, "stock": 50},
                        {"id": 2, "name": "Product B", "price": 149.99, "stock": 30},
                        {"id": 3, "name": "Product C", "price": 79.99, "stock": 100},
                    ],
                    "summary": "CSV file with 3 products containing id, name, price, and stock information",
                },
            },
        ]

        # Create 2-3 sessions per client
        for i, template in enumerate(session_templates[:3]):
            # Create session
            session = Session.objects.create(
                client=client,
                config=template["config"],
                messages=template["messages"],
                file_data=template.get("file_data"),
            )

            # Update last_activity to simulate different session ages
            session.last_activity = timezone.now() - timedelta(minutes=i * 5)
            session.save()

            message_count = len(template["messages"])
            has_file = "✓" if template.get("file_data") else "✗"

            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Session {i+1}: {str(session.id)[:8]}... "
                    f"({message_count} messages, File: {has_file})"
                )
            )

        # Create one expired session for testing
        expired_session = Session.objects.create(
            client=client,
            config={"aiProvider": "claude"},
            messages=[
                {"role": "user", "content": "This is an old session"},
            ],
        )
        expired_session.last_activity = timezone.now() - timedelta(hours=1)
        expired_session.save()

        self.stdout.write(
            self.style.WARNING(
                f"  ⚠ Expired Session: {str(expired_session.id)[:8]}... (for testing)"
            )
        )
