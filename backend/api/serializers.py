from rest_framework import serializers
from .models import Control, Evidence


class ControlSerializer(serializers.ModelSerializer):

    class Meta:
        model = Control
        fields = ["id", "name", "status", "created_by", "created_at"]
        read_only_fields = ["created_by", "created_at"]


class EvidenceSerializer(serializers.ModelSerializer):
    control = serializers.PrimaryKeyRelatedField(queryset=Control.objects.alive())

    class Meta:
        model = Evidence
        fields = [
            "id",
            "control",
            "name",
            "file",
            "status",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        control = attrs.get("control")
        if request and control and control.company_id != request.user.company_id:
            raise serializers.ValidationError({"control": "Control must belong to your company."})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request:
            validated_data["created_by"] = request.user
            validated_data["company"] = request.user.company
        # Default to rejected until validated by RAG agent
        if not validated_data.get("status"):
            validated_data["status"] = Evidence.STATUS_REJECTED
        return super().create(validated_data)

