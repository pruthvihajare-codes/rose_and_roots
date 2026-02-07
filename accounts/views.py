from django.shortcuts import render

def home(request):
    try:
        return render(request, 'home.html')
    except Exception as e:
        print("Exception caught:", e)
        raise

