# BigQuery Release Notes Viewer Runner

Write-Host "Checking python dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements.txt

Write-Host "Starting Flask Web Server..." -ForegroundColor Green
Write-Host "The application will be available at http://127.0.0.1:5000/" -ForegroundColor Yellow
python app.py
