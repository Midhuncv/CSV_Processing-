
from django import forms
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

class CSVUploadForm(forms.Form):
    """
    Form for uploading CSV files with validation
    """
    file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['csv'],
                message='Only CSV files are allowed.'
            )
        ],
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control',
                'accept': '.csv'
            }
        )
    )

    def clean_file(self):
        """
        Additional custom validation for uploaded file
        """
        file = self.cleaned_data.get('file')
        
        # Check file size (max 50MB)
        if file:
            if file.size > 50 * 1024 * 1024:  # 50MB
                raise ValidationError('File size must be under 50MB.')
            
            # Optional: Check file content
            try:
                # Read first few lines to ensure it looks like a CSV
                file.seek(0)
                first_line = file.readline().decode('utf-8').strip()
                if not first_line:
                    raise ValidationError('The CSV file appears to be empty.')
            except Exception:
                raise ValidationError('Unable to read the CSV file.')
            
            # Reset file pointer
            file.seek(0)
        
        return file