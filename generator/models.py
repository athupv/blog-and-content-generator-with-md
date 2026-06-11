from django.db import models
from django.contrib.auth.models import User

class GeneratedContent(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('blog', 'Blog Post'),
        ('product', 'Product Description'),
        ('caption', 'Social Media Caption'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_contents')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    prompt = models.TextField()
    generated_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_content_type_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class APIKeySetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='api_keys')
    openai_api_key = models.CharField(max_length=255, blank=True, default='')
    groq_api_key = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"API Keys for {self.user.username}"
