# core/views/auth.py (ou ajuste o caminho se preferir em outro lugar)
from rest_framework_simplejwt.views import TokenObtainPairView

from core.serializers.user import MyTokenObtainPairSerializer


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
