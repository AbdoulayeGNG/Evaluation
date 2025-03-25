
from django.contrib import admin
from django.urls import path, include
from Evaluation import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),  # URLs d'authentification Django
    path('', include('utilisateurs.urls')),
    path('', include('evaluationProf.urls')),

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



