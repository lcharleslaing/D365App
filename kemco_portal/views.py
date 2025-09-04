from django.shortcuts import render

def home(request):
    """Main homepage for Kemco Portal with all available tools"""
    return render(request, 'home.html')
