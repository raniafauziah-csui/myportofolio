import uuid
from django.db import models

# Create your models here.
class Experience(models.Model):
    EXPERIENCE_CHOICES = [
        ('internship', 'Internship'),
        ('research', 'Research'),
        ('volunteer', 'Volunteer'),
        ('part-time', 'Part-Time'),
        ('full-time', 'Full-Time'),
        ('freelance', 'Freelance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='full-time')
    thumbnail = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return self.title
    
    @property
    def is_ongoing(self):
        return self.ended_at is None


class Skill(models.Model):
    SKILL_CHOICES = [
        ('programming', 'Programming'),
        ('design', 'Graphic Design'),
        ('soft-skill', 'Soft Skill'),
        ('language', 'Language'),
        ('drawing', 'Drawing/Painting'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=SKILL_CHOICES, default='design')
    description = models.TextField()
    icon_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Achievement(models.Model):
    ACHIEVEMENT_CHOICES = [
        ('kti', 'Karya Tulis Ilmiah'),
        ('hackathon', 'Hackathon'),
        ('poster', 'Poster'),
        ('business case', 'Business Case'),
        ('olimpiade', 'Olimpiade'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=ACHIEVEMENT_CHOICES, default='hackathon')
    description = models.TextField()
    position = models.CharField(max_length=255)
    timestamp_achieved = models.PositiveIntegerField()
    timestamp_created = models.DateField(auto_now_add = True)

    def __str__(self):
        return self.name