import logging

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_providers import ai_provider
from chat.models import Session
from chat.services import ChatService

logger = logging.getLogger(__name__)


class ChatMessageView(APIView):
    """Send message to AI provider and get response"""

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
                session = Session.objects.get(id=session_id)

                # If client is authenticated, verify ownership
                if client and session.client != client:
                    return Response(
                        {"error": "Session not found. Please create a new session."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            except Session.DoesNotExist:
                return Response(
                    {"error": "Session not found. Please create a new session."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Update session config if provided
            if config:
                session.config = {**session.config, **config}

            # Add user message to conversation history
            user_message = {
                "role": "user",
                "content": message,
                "timestamp": timezone.now().timestamp() * 1000,
            }
            session.messages.append(user_message)

            # Get AI provider preference (session config > env setting > first available)
            provider_name = (
                session.config.get("aiProvider")
                or settings.AI_PROVIDER
                or next(iter(ai_provider._providers.keys()))
            )

            # Build context for AI
            conversation_history = session.messages[-10:]  # Last 10 messages
            context_prompt = ChatService.build_context_prompt(
                message, session.config, conversation_history, session.file_data
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

            # Add assistant response to conversation history
            assistant_message = {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": timezone.now().timestamp() * 1000,
            }
            session.messages.append(assistant_message)

            # Update session
            session.save()

            response_time = (timezone.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Chat Response - SessionID: {session_id}, ResponseTime: {response_time}ms, Provider: {ai_response.get('provider')}"
            )

            return Response(
                {
                    "response": assistant_response,
                    "sessionId": str(session.id),
                    "messageCount": len(session.messages),
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

    def get(self, request, session_id):
        logger.info(f"Chat Request - GET /history/{session_id}")
        client = request.auth

        try:
            session = Session.objects.get(id=session_id)

            # If client is authenticated, verify ownership
            if client and session.client != client:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {
                    "sessionId": str(session.id),
                    "messages": session.messages,
                    "messageCount": len(session.messages),
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

    def delete(self, request, session_id):
        logger.info(f"Chat Request - DELETE /history/{session_id}")
        client = request.auth

        try:
            session = Session.objects.get(id=session_id)

            # If client is authenticated, verify ownership
            if client and session.client != client:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

            previous_count = len(session.messages)

            session.messages = []
            session.save()

            logger.info(
                f"Chat Response - DELETE /history/{session_id} - Cleared {previous_count} messages"
            )

            return Response(
                {
                    "sessionId": str(session.id),
                    "status": "cleared",
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
