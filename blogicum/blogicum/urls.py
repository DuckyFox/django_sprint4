from django.contrib import admin
from django.urls import include, reverse_lazy, path
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import CreateView

from django.contrib.auth.forms import UserCreationForm

handler404 = 'core.views.page_not_found'
handler403 = 'core.views.access_denied'
handler500 = 'core.views.server_error'

urlpatterns = [
    path('', include('blog.urls', namespace='blog')),
    path('pages/', include('pages.urls', namespace='pages')),
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/registration', CreateView.as_view(
        template_name='registration/registration_form.html',
        form_class=UserCreationForm,
        success_url=reverse_lazy('blog:index'),
        ), name='registration'
        )
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
