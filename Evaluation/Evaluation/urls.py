from django.contrib import admin
from django.urls import path, include
from Evaluation import settings
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),  # URLs d'authentification Django
    path('', include(('utilisateurs.urls', 'utilisateurs'), namespace='utilisateurs')),
    path('', include(('evaluationProf.urls', 'evaluationProf'), namespace='evaluationProf')),
    path('', include(('etudiants.urls', 'etudiants'), namespace='etudiants')),
    path('prof/', include(('prof.urls', 'prof'), namespace='prof')),
    path('administration/', include(('administration.urls', 'administration'), namespace='administration')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



