# aura/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    # The homepage is now handled by the landing app
    path('', include('landing.urls')), 
    # The main application now lives under the /app/ prefix
    path('app/', include('core.urls')), 
    path('forge/', include('forge.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)