# aura_supervisor/models.py

import uuid
from django.db import models

class Job(models.Model):
    """Represents a single operational task AURA is supervising."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        AWAITING_APPROVAL = 'AWAITING_APPROVAL', 'Awaiting Approval'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default="New Operational Job")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    identified_component = models.CharField(max_length=255, blank=True, null=True)
    final_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.id} - {self.status}"


class JobLog(models.Model):
    """Stores a log entry for a specific step in a Job's workflow."""
    class Source(models.TextChoices):
        SUPERVISOR = 'SUPERVISOR', 'Aura Supervisor'
        IDENTIFIER = 'IDENTIFIER', 'Identifier Agent'
        PROCEDURE = 'PROCEDURE', 'Procedure Agent'
        SUMMARIZER = 'SUMMARIZER', 'Summarizer Agent'
        USER = 'USER', 'Human Technician'

    job = models.ForeignKey(Job, related_name='logs', on_delete=models.CASCADE)
    source = models.CharField(max_length=20, choices=Source.choices)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, null=True) # To store raw responses

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.timestamp}] [{self.source}] {self.message}"