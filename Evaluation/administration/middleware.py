from django.shortcuts import redirect
from django.contrib import messages

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/administration/') and request.user.is_authenticated:
            if not request.user.is_staff:
                messages.error(request, "Vous n'avez pas accès à cette section")
                return redirect('home')
                
        return self.get_response(request)