import os

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import FileUpload, Session
from chat.services import FileProcessor
from core.authentication import APIKeyAuthentication, IsClientAuthenticated


class FileUploadView(APIView):
    """Upload and process file"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]
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
            client = request.auth
            try:
                session = Session.objects.get(id=session_id, client=client)
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

                # Deactivate any existing files for this session
                session.uploaded_files.filter(is_active=True).update(is_active=False)

                # Create FileUpload record
                file_upload = FileUpload.objects.create(
                    session=session,
                    original_name=uploaded_file.name,
                    file_path=str(file_path),
                    file_type=processed_data["type"],
                    file_size=processed_data["size"],
                    processed_data=processed_data.get("data", {}),
                    summary=processed_data.get("summary", ""),
                    is_active=True,
                )

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

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def get(self, request, session_id):
        client = request.auth

        try:
            session = Session.objects.get(id=session_id, client=client)

            # Get active file upload for this session
            active_file = session.uploaded_files.filter(is_active=True).first()

            if not active_file:
                return Response(
                    {"error": "No file uploaded for this session"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "fileName": active_file.original_name,
                    "fileType": active_file.file_type,
                    "fileSize": active_file.file_size,
                    "uploadedAt": active_file.uploaded_at.isoformat(),
                    "summary": active_file.summary,
                }
            )

        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )


class FileQueryView(APIView):
    """Query file data"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def post(self, request, session_id):
        client = request.auth
        query = request.data.get("query")

        if not query:
            return Response(
                {"error": "Missing query parameter"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = Session.objects.get(id=session_id, client=client)

            # Get active file upload for this session
            active_file = session.uploaded_files.filter(is_active=True).first()

            if not active_file:
                return Response(
                    {"error": "No file uploaded for this session"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Build file_data dict for FileProcessor
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

            # Query the file data
            query_result = FileProcessor.query_data(file_data, query)

            return Response(
                {
                    "query": query,
                    "results": query_result,
                    "fileName": active_file.original_name,
                    "fileType": active_file.file_type,
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

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def delete(self, request, session_id):
        client = request.auth

        try:
            session = Session.objects.get(id=session_id, client=client)

            # Get active file upload for this session
            active_file = session.uploaded_files.filter(is_active=True).first()

            if not active_file:
                return Response(
                    {"error": "No file data to delete"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Clean up physical file
            if active_file.file_path and os.path.exists(active_file.file_path):
                try:
                    os.unlink(active_file.file_path)
                except Exception as e:
                    print(f"Failed to delete physical file: {e}")

            # Mark file as inactive (soft delete)
            active_file.is_active = False
            active_file.save()

            return Response(
                {"success": True, "message": "File data deleted successfully"}
            )

        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )
