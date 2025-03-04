import os
import pandas as pd
from celery import shared_task
from django.core.files.storage import default_storage
from django.conf import settings

from .models import CSVUpload, ProcessedData

@shared_task
def process_csv_file(upload_id):
    """
    Celery task to process uploaded CSV file
    """
    try:
        # Retrieve the upload record
        csv_upload = CSVUpload.objects.get(id=upload_id)
        
        # Read the CSV file
        file_path = csv_upload.file.path
        df = pd.read_csv(file_path)
        
        # Validate DataFrame
        if df.empty:
            raise ValueError("The CSV file is empty")
        
        # Perform calculations
        calculations = calculate_csv_metrics(df)
        
        # Create or update ProcessedData
        processed_data, created = ProcessedData.objects.get_or_create(
            upload=csv_upload,
            defaults=calculations
        )
        
        # If not created, update existing record
        if not created:
            for key, value in calculations.items():
                setattr(processed_data, key, value)
        
        processed_data.save()
        
        # Mark upload as processed
        csv_upload.processed = True
        csv_upload.save()
        
        return {
            'status': 'success',
            'upload_id': str(csv_upload.id),
            'metrics': calculations
        }
    
    except Exception as e:
        # Log the error
        print(f"CSV Processing Error: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

def calculate_csv_metrics(df):
    """
    Calculate various metrics from the DataFrame
    """
    # Ensure numeric columns
    numeric_columns = ['Sales', 'Quantity', 'Discount', 'Profit']
    
    # Validate numeric columns exist
    for col in numeric_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in CSV")
    
    # Convert to numeric, coerce errors to NaN
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate metrics
    metrics = {
        'total_revenue': df['Sales'].sum(),
        'avg_discount': df['Discount'].mean(),
        'best_selling_product': df.groupby('Product')['Quantity'].sum().idxmax(),
        'most_profitable_product': df.groupby('Product')['Profit'].sum().idxmax(),
        'max_discount_product': df.loc[df['Discount'].idxmax(), 'Product']
    }
    
    return metrics

@shared_task
def cleanup_old_uploads():
    """
    Periodic task to clean up old CSV uploads
    """
    # Remove uploads older than 7 days
    from django.utils import timezone
    from datetime import timedelta
    
    # Find and delete old, unprocessed uploads
    old_uploads = CSVUpload.objects.filter(
        uploaded_at__lt=timezone.now() - timedelta(days=7),
        processed=False
    )
    
    # Delete associated files
    for upload in old_uploads:
        # Remove file from storage
        if upload.file:
            default_storage.delete(upload.file.path)
        
        # Delete database record
        upload.delete()
    
    return f"Cleaned {old_uploads.count()} old uploads"
