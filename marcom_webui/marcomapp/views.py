from django.shortcuts import render

# Create your views here.

def index(request):
    # Render the homepage or filter page for Marcom-Components
    return render(request, 'marcomapp/index.html')

