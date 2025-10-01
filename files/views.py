import os

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from chat_sessions.models import Session
from core.file_processor import FileProcessor


class FileUploadView(APIView):
    """Upload and process file"""

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        session_id = request.data.get("sessionId")
        uploaded_file = request.FILES.get("file")

        if not session_id:
            return Response(
                {"error": "Missing sessionId"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not uploaded_file:
            return Response(
                {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get session
            try:
                session = Session.objects.get(id=session_id)
            except Session.DoesNotExist:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Validate file type
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            if file_ext not in [".json", ".csv"]:
                return Response(
                    {"error": "Only JSON and CSV files are allowed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Save file
            upload_dir = settings.MEDIA_ROOT / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path = upload_dir / f"{session_id}_{uploaded_file.name}"
            with open(file_path, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Process file
            try:
                if file_ext == ".json":
                    processed_data = FileProcessor.process_json(str(file_path))
                elif file_ext == ".csv":
                    processed_data = FileProcessor.process_csv(str(file_path))
                else:
                    raise ValueError("Unsupported file type")

                # Store file data in session
                session.file_data = {
                    **processed_data,
                    "originalName": uploaded_file.name,
                    "uploadedAt": timezone.now().timestamp() * 1000,
                    "filePath": str(file_path),
                }
                session.save()

                return Response(
                    {
                        "success": True,
                        "fileName": uploaded_file.name,
                        "fileType": processed_data["type"],
                        "fileSize": processed_data["size"],
                        "summary": processed_data["summary"],
                        "sessionId": str(session.id),
                        "message": f'File "{uploaded_file.name}" has been uploaded and processed successfully. You can now ask questions about the data.',
                    }
                )

            except Exception as processing_error:
                # Clean up file on processing error
                if file_path.exists():
                    os.unlink(file_path)
                raise processing_error

        except Exception as e:
            return Response(
                {"error": "Failed to process file", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FileInfoView(APIView):
    """Get file information for a session"""

    def get(self, request, session_id):
        try:
            session = Session.objects.get(id=session_id)

            if not session.file_data:
                return Response(
                    {"error": "No file uploaded for this session"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "fileName": session.file_data.get("originalName"),
                    "fileType": session.file_data.get("type"),
                    "fileSize": session.file_data.get("size"),
                    "uploadedAt": timezone.datetime.fromtimestamp(
                        session.file_data.get("uploadedAt") / 1000
                    ).isoformat(),
                    "summary": session.file_data.get("summary"),
                }
            )

        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )


class FileQueryView(APIView):
    """Query file data"""

    def post(self, request, session_id):
        query = request.data.get("query")

        if not query:
            return Response(
                {"error": "Missing query parameter"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = Session.objects.get(id=session_id)

            if not session.file_data:
                return Response(
                    {"error": "No file uploaded for this session"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Query the file data
            query_result = FileProcessor.query_data(session.file_data, query)

            return Response(
                {
                    "query": query,
                    "results": query_result,
                    "fileName": session.file_data.get("originalName"),
                    "fileType": session.file_data.get("type"),
                }
            )

        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "Failed to query file data", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FileDeleteView(APIView):
    """Delete file data from session"""

    def delete(self, request, session_id):
        try:
            session = Session.objects.get(id=session_id)

            if not session.file_data:
                return Response(
                    {"error": "No file data to delete"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Clean up physical file
            file_path = session.file_data.get("filePath")
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Failed to delete physical file: {e}")

            # Remove file data from session
            session.file_data = None
            session.save()

            return Response(
                {"success": True, "message": "File data deleted successfully"}
            )

        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )
