from django.db import models
import uuid

class CSVUpload(models.Model):
    """
    Model to track CSV file uploads and their processing status
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='csv_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    filename = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.filename} - {self.uploaded_at}"

class ProcessedData(models.Model):
    """
    Model to store processed CSV data results
    """
    upload = models.OneToOneField(CSVUpload, on_delete=models.CASCADE)
    total_revenue = models.FloatField(null=True)
    avg_discount = models.FloatField(null=True)
    best_selling_product = models.CharField(max_length=255, null=True)
    most_profitable_product = models.CharField(max_length=255, null=True)
    max_discount_product = models.CharField(max_length=255, null=True)
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Processed Results for {self.upload.filename}"