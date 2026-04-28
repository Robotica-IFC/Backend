from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from core.views import (
    AlunoViewSet,
    EstadoViewSet,
    InstituicaoViewSet,
    MyTokenObtainPairView,
    ProfessorViewSet,
    UserRegistrationView,
    UserViewSet,
)
from uploader.router import router as uploader_router

router = DefaultRouter()

router.register(r'alunos', AlunoViewSet, basename='alunos')
router.register(r'estados', EstadoViewSet, basename='estados')
router.register(r'instituicoes', InstituicaoViewSet, basename='instituicoes')
router.register(r'usuarios', UserViewSet, basename='usuarios')
router.register(r'professores', ProfessorViewSet, basename='professores')

urlpatterns = [
    path('admin/', admin.site.urls),
    # OpenAPI 3
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/doc/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path('api/media/', include(uploader_router.urls)),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
    # Autenticação JWT
path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'), path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Registro de usuários
    path('api/registro/', UserRegistrationView.as_view(), name='user_registration'),
    # API
    path('api/', include(router.urls)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
