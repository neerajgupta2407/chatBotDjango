from rest_framework import serializers

from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""

    class Meta:
        model = Client
        fields = ["id", "name", "email", "api_key", "config", "is_active", "created_at"]
        read_only_fields = ["id", "api_key", "created_at"]


class ClientConfigSerializer(serializers.Serializer):
    """Serializer for updating client configuration"""

    config = serializers.JSONField()

    def validate_config(self, value):
        """Validate config is a dictionary"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a JSON object")
        return value
