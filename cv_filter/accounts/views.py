from django.contrib.auth import authenticate, get_user_model
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegisterSerializer

User = get_user_model()


class RegisterView(APIView):
    """
    API endpoint to register a user and return JWT tokens.
    """

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': RegisterSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    API endpoint to log in and return JWT tokens.
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if not user:
            return Response(
                {'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED
            )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': RegisterSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        )


class LoginPageView(TemplateView):
    template_name = 'accounts/login.html'


class RegisterPageView(TemplateView):
    template_name = 'accounts/register.html'
