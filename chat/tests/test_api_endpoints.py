"""
Test cases for Chat API endpoints after migration to normalized Message model.

Tests:
    - Session creation
    - Message sending and storage in Message model
    - Message history retrieval from Message model
    - Message clearing (deleting Message objects)
"""

from unittest.mock import AsyncMock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from chat.models import FileUpload, Message, Session
from clients.models import Client


class ChatAPIEndpointsTestCase(TestCase):
    """Test all chat API endpoints with normalized Message model."""

    def setUp(self):
        """Set up test client and data."""
        self.client_api = APIClient()

        # Create a test client
        self.test_client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            config={
                "bot_name": "TestBot",
                "primary_color": "#ff0000",
            },
        )

        # Set API key header
        self.api_key = self.test_client.api_key
        self.client_api.credentials(HTTP_X_API_KEY=self.api_key)

    def test_session_creation(self):
        """Test POST /api/chat/sessions/create."""
        response = self.client_api.post(
            "/api/chat/sessions/create",
            {"config": {"aiProvider": "claude"}},
            format="json",
        )

        self.assertEqual(
            response.status_code, 201
        )  # 201 Created is correct for resource creation
        self.assertIn("sessionId", response.data)
        self.assertIn("config", response.data)
        self.assertEqual(response.data["status"], "created")

        # Verify session was created in database
        session_id = response.data["sessionId"]
        session = Session.objects.get(id=session_id)
        self.assertEqual(session.client, self.test_client)
        self.assertEqual(session.config.get("aiProvider"), "claude")

    def test_message_storage_in_model(self):
        """Test that messages are stored in Message model (not JSONField)."""
        # Create a session
        session = Session.objects.create(
            client=self.test_client,
            config={"aiProvider": "claude"},
        )

        # Directly create messages using the Message model
        user_msg = Message.objects.create(
            session=session,
            role="user",
            content="Hello, how are you?",
        )

        assistant_msg = Message.objects.create(
            session=session,
            role="assistant",
            content="I'm doing great, thank you!",
        )

        # Verify messages are stored in database
        messages = Message.objects.filter(session=session).order_by("timestamp")
        self.assertEqual(messages.count(), 2)

        # Verify message content
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hello, how are you?")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, "I'm doing great, thank you!")

        # Verify that Session model doesn't have messages JSONField anymore
        # (this would fail if legacy field still exists)
        self.assertFalse(
            hasattr(session, "messages")
            and isinstance(getattr(session, "messages", None), list)
        )

    def test_message_history_retrieval(self):
        """Test GET /api/chat/messages/history/{session_id} - retrieves from Message model."""
        # Create session with messages
        session = Session.objects.create(
            client=self.test_client,
            config={"aiProvider": "claude"},
        )

        # Create messages directly in Message model
        Message.objects.create(
            session=session,
            role="user",
            content="First message",
        )
        Message.objects.create(
            session=session,
            role="assistant",
            content="First response",
        )
        Message.objects.create(
            session=session,
            role="user",
            content="Second message",
        )

        # Retrieve history
        response = self.client_api.get(
            f"/api/chat/messages/history/{session.id}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("messages", response.data)
        self.assertEqual(len(response.data["messages"]), 3)
        self.assertEqual(response.data["messageCount"], 3)

        # Check message order
        messages = response.data["messages"]
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "First message")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[2]["role"], "user")

    def test_message_clearing(self):
        """Test DELETE /api/chat/messages/clear/{session_id} - deletes Message objects."""
        # Create session with messages
        session = Session.objects.create(
            client=self.test_client,
            config={"aiProvider": "claude"},
        )

        # Create messages
        Message.objects.create(session=session, role="user", content="Message 1")
        Message.objects.create(session=session, role="assistant", content="Response 1")
        Message.objects.create(session=session, role="user", content="Message 2")

        # Verify messages exist
        self.assertEqual(Message.objects.filter(session=session).count(), 3)

        # Clear messages
        response = self.client_api.delete(
            f"/api/chat/messages/clear/{session.id}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "cleared")
        self.assertEqual(response.data["messagesCleared"], 3)

        # Verify messages were deleted from Message model
        self.assertEqual(Message.objects.filter(session=session).count(), 0)

    def test_session_not_found(self):
        """Test endpoints with non-existent session ID."""
        fake_session_id = "00000000-0000-0000-0000-000000000000"

        # Test history retrieval
        response = self.client_api.get(
            f"/api/chat/messages/history/{fake_session_id}",
        )
        self.assertEqual(response.status_code, 404)

        # Test message sending
        response = self.client_api.post(
            "/api/chat/messages/send",
            {
                "sessionId": fake_session_id,
                "message": "Hello",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        # Test clearing
        response = self.client_api.delete(
            f"/api/chat/messages/clear/{fake_session_id}",
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_access_without_api_key(self):
        """Test that endpoints require API key authentication."""
        # Create session
        session = Session.objects.create(
            client=self.test_client,
            config={"aiProvider": "claude"},
        )

        # Clear credentials (remove API key)
        self.client_api.credentials()

        # Test session creation
        response = self.client_api.post(
            "/api/chat/sessions/create",
            {"config": {"aiProvider": "claude"}},
            format="json",
        )
        self.assertEqual(response.status_code, 403)  # Forbidden without auth

        # Test message history
        response = self.client_api.get(
            f"/api/chat/messages/history/{session.id}",
        )
        self.assertEqual(response.status_code, 403)  # Forbidden without auth

        # Test message sending
        response = self.client_api.post(
            "/api/chat/messages/send",
            {"sessionId": str(session.id), "message": "Hello"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)  # Forbidden without auth

        # Test clearing messages
        response = self.client_api.delete(
            f"/api/chat/messages/clear/{session.id}",
        )
        self.assertEqual(response.status_code, 403)  # Forbidden without auth

    def test_unauthorized_access_with_invalid_api_key(self):
        """Test that endpoints reject invalid API keys."""
        # Set invalid API key
        self.client_api.credentials(HTTP_X_API_KEY="invalid_key_12345")

        # Test session creation
        response = self.client_api.post(
            "/api/chat/sessions/create",
            {"config": {"aiProvider": "claude"}},
            format="json",
        )
        self.assertEqual(response.status_code, 403)  # Forbidden with invalid key

        # Test message history
        session = Session.objects.create(
            client=self.test_client,
            config={"aiProvider": "claude"},
        )
        response = self.client_api.get(
            f"/api/chat/messages/history/{session.id}",
        )
        self.assertEqual(response.status_code, 403)  # Forbidden with invalid key

    def test_message_count_endpoint(self):
        """Test that message count is accurate after multiple operations."""
        session = Session.objects.create(
            client=self.test_client,
            config={"aiProvider": "claude"},
        )

        # Create 5 messages
        for i in range(5):
            Message.objects.create(
                session=session,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
            )

        # Get history
        response = self.client_api.get(
            f"/api/chat/messages/history/{session.id}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["messageCount"], 5)
        self.assertEqual(len(response.data["messages"]), 5)

    def test_message_ordering(self):
        """Test that messages are returned in chronological order."""
        session = Session.objects.create(
            client=self.test_client,
            config={"aiProvider": "claude"},
        )

        # Create messages with explicit timestamps
        now = timezone.now()
        Message.objects.create(
            session=session,
            role="user",
            content="Third message",
            timestamp=now,
        )
        Message.objects.create(
            session=session,
            role="user",
            content="First message",
            timestamp=now - timezone.timedelta(minutes=2),
        )
        Message.objects.create(
            session=session,
            role="user",
            content="Second message",
            timestamp=now - timezone.timedelta(minutes=1),
        )

        # Get history
        response = self.client_api.get(
            f"/api/chat/messages/history/{session.id}",
        )

        self.assertEqual(response.status_code, 200)
        messages = response.data["messages"]

        # Check chronological order
        self.assertEqual(messages[0]["content"], "First message")
        self.assertEqual(messages[1]["content"], "Second message")
        self.assertEqual(messages[2]["content"], "Third message")

    def test_cross_client_isolation(self):
        """Test that clients cannot access other clients' sessions."""
        # Create another client
        other_client = Client.objects.create(
            name="Other Client",
            email="other@example.com",
        )

        # Create session for other client
        other_session = Session.objects.create(
            client=other_client,
            config={"aiProvider": "claude"},
        )

        Message.objects.create(
            session=other_session,
            role="user",
            content="Secret message",
        )

        # Try to access other client's session with our API key
        response = self.client_api.get(
            f"/api/chat/messages/history/{other_session.id}",
        )

        # Should return 404 (session not found for this client)
        self.assertEqual(response.status_code, 404)

    def test_empty_session_history(self):
        """Test retrieving history from session with no messages."""
        session = Session.objects.create(
            client=self.test_client,
            config={"aiProvider": "claude"},
        )

        response = self.client_api.get(
            f"/api/chat/messages/history/{session.id}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["messageCount"], 0)
        self.assertEqual(len(response.data["messages"]), 0)
