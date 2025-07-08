# Aura/core/models.py

import uuid
from django.db import models

def user_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/input_images/<job_id>/<filename>
    return f'input_images/{instance.job.id}/{filename}'

def aura_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/annotated_images/<job_id>/<filename>
    return f'annotated_images/{instance.job.id}/{filename}'

class Job(models.Model):
    """
    Represents a single "Session" or operational task AURA is supervising.
    This is the parent object for a full conversation.
    """
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED_SUCCESS = 'COMPLETED_SUCCESS', 'Completed Successfully'
        COMPLETED_FAILURE = 'COMPLETED_FAILURE', 'Completed with Failure'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default="New AURA Session")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    final_report_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.id} - {self.status}"

class Interaction(models.Model):
    """
    Represents a single "turn" in the conversation between the user and Aura,
    belonging to a specific Job (Session).
    """
    class Source(models.TextChoices):
        USER = 'USER', 'Human Technician'
        AURA = 'AURA', 'Aura Assistant'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, related_name='interactions', on_delete=models.CASCADE)
    source = models.CharField(max_length=20, choices=Source.choices)
    
    # User's Input for this turn
    user_text_input = models.TextField(blank=True, null=True)
    user_image_input = models.ImageField(upload_to=user_image_path, blank=True, null=True)

    # Aura's Response for this turn
    aura_text_response = models.TextField(blank=True, null=True)
    aura_annotated_image = models.ImageField(upload_to=aura_image_path, blank=True, null=True)
    
    # Metadata for the turn
    timestamp = models.DateTimeField(auto_now_add=True)
    parsed_intent = models.CharField(max_length=100, blank=True, null=True) # e.g., "FETCH_PROCEDURE"

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Interaction {self.id} for Job {self.job.id}"

# Aura/core/models.py
# ... (at the end of the file, after your Job and Interaction models) ...

class Procedure(models.Model):
    """
    A local cache of an operational procedure, synced from a primary
    source like Snowflake. Used as a resilient offline fallback.
    """
    procedure_id = models.CharField(max_length=50, primary_key=True)
    component_name = models.CharField(max_length=255, unique=True)
    # JSONField is perfect for storing lists of steps and warnings
    steps = models.JSONField(default=list)
    safety_warnings = models.JSONField(default=list)
    last_synced = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.procedure_id}: {self.component_name}"