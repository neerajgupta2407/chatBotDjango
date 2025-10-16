import logging

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_providers import ai_provider
from chat.models import Message, Session
from chat.services import ChatService
from core.authentication import APIKeyAuthentication, IsClientAuthenticated

logger = logging.getLogger(__name__)


class ChatMessageView(APIView):
    """Send message to AI provider and get response"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def post(self, request):
        start_time = timezone.now()
        session_id = request.data.get("sessionId")
        message = request.data.get("message")
        config = request.data.get("config")

        logger.info(
            f"Chat Request - POST /message - SessionID: {session_id}, MessageLength: {len(message) if message else 0}"
        )

        if not session_id or not message:
            return Response(
                {"error": "Missing required fields: sessionId and message"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get session
            client = request.auth
            try:
                session = Session.objects.get(id=session_id, client=client)
            except Session.DoesNotExist:
                return Response(
                    {"error": "Session not found. Please create a new session."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Update session config if provided
            if config:
                session.config = {**session.config, **config}
                session.save(update_fields=["config"])

            # Save user message to Message model
            user_msg_obj = Message.objects.create(
                session=session,
                role="user",
                content=message,
            )

            # Get AI provider preference (session config > env setting > first available)
            provider_name = (
                session.config.get("aiProvider")
                or settings.AI_PROVIDER
                or next(iter(ai_provider._providers.keys()))
            )

            # Build context for AI using normalized messages (last 10)
            conversation_history = [
                msg.to_dict()
                for msg in session.conversation_messages.order_by("-timestamp")[:10]
            ]
            # Reverse to get chronological order
            conversation_history.reverse()

            # Get file data from FileUpload model (if any active files exist)
            file_data = None
            active_file = session.uploaded_files.filter(is_active=True).first()
            if active_file:
                file_data = {
                    "type": active_file.file_type,
                    "size": active_file.file_size,
                    "data": active_file.processed_data,
                    "summary": (
                        active_file.summary
                        if isinstance(active_file.summary, dict)
                        else {"description": active_file.summary}
                    ),
                }

            # Get client's custom system prompt if configured
            system_prompt = client.config.get("system_prompt")

            context_prompt = ChatService.build_context_prompt(
                message, session.config, conversation_history, file_data, system_prompt
            )

            logger.info(
                f"Context Prompt Token Estimate: {ChatService.estimate_token_count(context_prompt)}"
            )

            # Prepare messages for AI provider
            ai_messages = [{"role": "user", "content": context_prompt}]

            # Call AI provider (synchronous wrapper for async)
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            ai_response = loop.run_until_complete(
                ai_provider.generate_response(
                    provider_name,
                    ai_messages,
                    {
                        "model": session.config.get("model"),
                        "maxTokens": session.config.get("maxTokens", 1000),
                    },
                )
            )

            assistant_response = ai_response["content"]

            # Save assistant response to Message model
            assistant_msg_obj = Message.objects.create(
                session=session,
                role="assistant",
                content=assistant_response,
                metadata={
                    "provider": ai_response.get("provider"),
                    "model": ai_response.get("model"),
                },
            )

            # Update session last_activity
            session.save()

            response_time = (timezone.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Chat Response - SessionID: {session_id}, ResponseTime: {response_time}ms, Provider: {ai_response.get('provider')}"
            )

            # Get total message count
            message_count = session.conversation_messages.count()

            return Response(
                {
                    "response": assistant_response,
                    "sessionId": str(session.id),
                    "messageCount": message_count,
                    "provider": ai_response.get("provider"),
                    "model": ai_response.get("model"),
                    "timestamp": timezone.now().isoformat(),
                }
            )

        except ValueError as e:
            logger.error(f"Chat Error - ValueError: {str(e)}")
            return Response(
                {"error": str(e), "details": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Chat Error - Exception: {str(e)}")
            error_message = "Failed to process message"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                error_message = "API authentication failed"
                status_code = status.HTTP_401_UNAUTHORIZED
            elif "rate limit" in str(e).lower():
                error_message = "Rate limit exceeded"
                status_code = status.HTTP_429_TOO_MANY_REQUESTS

            return Response(
                {"error": error_message, "details": str(e)}, status=status_code
            )


class ChatHistoryView(APIView):
    """Get conversation history"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def get(self, request, session_id):
        logger.info(f"Chat Request - GET /history/{session_id}")
        client = request.auth

        try:
            session = Session.objects.get(id=session_id, client=client)

            # Get messages from Message model
            messages = [msg.to_dict() for msg in session.conversation_messages.all()]

            return Response(
                {
                    "sessionId": str(session.id),
                    "messages": messages,
                    "messageCount": len(messages),
                }
            )
        except Session.DoesNotExist:
            logger.info(
                f"Chat Response - GET /history/{session_id} - Session not found"
            )
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )


class ClearHistoryView(APIView):
    """Clear conversation history"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def delete(self, request, session_id):
        logger.info(f"Chat Request - DELETE /history/{session_id}")
        client = request.auth

        try:
            session = Session.objects.get(id=session_id, client=client)

            # Get count before deletion
            previous_count = session.conversation_messages.count()

            # Delete all messages from Message model
            session.conversation_messages.all().delete()

            logger.info(
                f"Chat Response - DELETE /history/{session_id} - Cleared {previous_count} messages"
            )

            return Response(
                {
                    "sessionId": str(session.id),
                    "status": "cleared",
                    "messagesCleared": previous_count,
                    "timestamp": timezone.now().isoformat(),
                }
            )
        except Session.DoesNotExist:
            logger.info(
                f"Chat Response - DELETE /history/{session_id} - Session not found"
            )
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )
