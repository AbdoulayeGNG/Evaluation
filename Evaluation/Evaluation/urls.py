from django.contrib import admin
from django.urls import path, include
from Evaluation import settings
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Add this line
    path('admin/', admin.site.urls),
    # path('accounts/', include('django.contrib.auth.urls')),  # URLs d'authentification Django
    path('', include(('utilisateurs.urls', 'utilisateurs'), namespace='utilisateurs')),
    path('', include(('evaluationProf.urls', 'evaluationProf'), namespace='evaluationProf')),
    path('', include(('etudiants.urls', 'etudiants'), namespace='etudiants')),
    path('prof/', include(('prof.urls', 'prof'), namespace='prof')),
    path('administration/', include(('administration.urls', 'administration'), namespace='administration')),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



