import pandas as pd
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
import os

from .models import CSVUpload, ProcessedData
from .forms import CSVUploadForm
from .tasks import process_csv_file

class CSVUploadView(View):
    template_name = 'uploader/upload.html'

    def get(self, request):
        form = CSVUploadForm()
        recent_uploads = CSVUpload.objects.order_by('-uploaded_at')[:5]
        return render(request, self.template_name, {
            'form': form,
            'recent_uploads': recent_uploads
        })

    def post(self, request):
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the uploaded file
            csv_file = request.FILES['file']
            
            # Validate file extension
            if not csv_file.name.endswith('.csv'):
                return JsonResponse({
                    'error': 'Only CSV files are allowed.'
                }, status=400)

            # Save file to storage
            file_path = default_storage.save(
                f'csv_uploads/{csv_file.name}', 
                csv_file
            )
            
            # Create CSV Upload record
            csv_upload = CSVUpload.objects.create(
                file=file_path,
                filename=csv_file.name
            )

            # Trigger Celery task for processing
            task = process_csv_file.delay(str(csv_upload.id))

            return JsonResponse({
                'message': 'File uploaded successfully',
                'task_id': str(task.id),
                'upload_id': str(csv_upload.id)
            })
        
        return JsonResponse({
            'errors': form.errors
        }, status=400)

class CSVResultsView(TemplateView):
    template_name = 'uploader/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the most recent upload
        recent_upload = CSVUpload.objects.order_by('-uploaded_at').first()
        
        if recent_upload:
            # Try to get processed data
            try:
                processed_data = ProcessedData.objects.get(upload=recent_upload)
                context['processed_data'] = processed_data
            except ProcessedData.DoesNotExist:
                context['processed_data'] = None
            
            # Read CSV data for display
            try:
                df = pd.read_csv(recent_upload.file.path)
                context['csv_data'] = df.to_dict('records')
                context['columns'] = df.columns.tolist()
            except Exception as e:
                context['error'] = str(e)
        
        return context

class DataSearchView(View):
    def get(self, request):
        # Get search query and file path
        search_query = request.GET.get('search', '').strip()
        recent_upload = CSVUpload.objects.order_by('-uploaded_at').first()
        
        if not recent_upload:
            return JsonResponse({'error': 'No recent uploads found'}, status=404)
        
        try:
            # Read CSV and filter
            df = pd.read_csv(recent_upload.file.path)
            
            # Case-insensitive product name search
            if search_query:
                filtered_df = df[df['Product'].str.contains(search_query, case=False, na=False)]
            else:
                filtered_df = df
            
            # Convert to list of dictionaries
            results = filtered_df.to_dict('records')
            
            return JsonResponse({
                'data': results,
                'total_records': len(results)
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class CalculationSummaryView(View):
    def get(self, request):
        recent_upload = CSVUpload.objects.order_by('-uploaded_at').first()
        
        if not recent_upload:
            return JsonResponse({'error': 'No recent uploads found'}, status=404)
        
        try:
            # Retrieve processed data
            processed_data = ProcessedData.objects.get(upload=recent_upload)
            
            return JsonResponse({
                'total_revenue': processed_data.total_revenue,
                'avg_discount': processed_data.avg_discount,
                'best_selling_product': processed_data.best_selling_product,
                'most_profitable_product': processed_data.most_profitable_product,
                'max_discount_product': processed_data.max_discount_product
            })
        
        except ProcessedData.DoesNotExist:
            return JsonResponse({'error': 'Calculations not completed yet'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)