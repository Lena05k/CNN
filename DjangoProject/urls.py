from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.scoreImagePage, name='scoreImagePage'),
    path('predictImage', views.predictImage, name='predictImage'),
    # ДЗ 2
    path('api/segment',     views.segment_image,    name='segment_image'),
    path('api/clip-search', views.clip_card_search, name='clip_card_search'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)