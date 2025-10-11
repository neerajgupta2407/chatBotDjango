"""
Workflow automation models.
"""

import uuid

from django.db import models


class Workflow(models.Model):
    """Automated workflow configuration"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="workflows"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    trigger_type = models.CharField(
        max_length=50,
        choices=[
            ("manual", "Manual"),
            ("chat_command", "Chat Command"),
            ("schedule", "Scheduled"),
            ("webhook", "Webhook"),
        ],
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey("users.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflows"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class WorkflowStep(models.Model):
    """Individual step in a workflow"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name="steps"
    )

    step_order = models.IntegerField()
    step_type = models.CharField(
        max_length=50,
        choices=[
            ("ai_generation", "AI Generation"),
            ("api_call", "API Call"),
            ("data_transform", "Data Transform"),
            ("condition", "Conditional Logic"),
            ("email", "Send Email"),
        ],
    )

    config = models.JSONField(default=dict)

    class Meta:
        db_table = "workflow_steps"
        ordering = ["step_order"]

    def __str__(self):
        return f"{self.workflow.name} - Step {self.step_order}"


class WorkflowRun(models.Model):
    """Execution record of a workflow"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name="runs"
    )
    session = models.ForeignKey(
        "chat.Session", on_delete=models.CASCADE, null=True, blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
    )

    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "workflow_runs"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.workflow.name} - {self.status}"
