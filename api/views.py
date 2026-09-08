from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from core.models import Branch, StaffProfile

from api.serializers import (
    UserSerializer, StaffProfileSerializer, BranchSerializer
)

class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            if hasattr(user, 'profile') and user.profile.status == 'inactive':
                return Response({'detail': 'User account is inactive'}, status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            role = user.profile.role if hasattr(user, 'profile') else ('ADMIN' if user.is_superuser else 'STAFF')
            branch_id = user.profile.branch.id if hasattr(user, 'profile') and user.profile.branch else None

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': role,
                    'branch_id': branch_id
                }
            })
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class MeAPIView(APIView):
    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        serializer = StaffProfileSerializer(profile) if profile else None
        return Response({
            'user': UserSerializer(request.user).data,
            'profile': serializer.data if serializer else None
        })


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class StaffProfileViewSet(viewsets.ModelViewSet):
    queryset = StaffProfile.objects.select_related('user', 'branch').all()
    serializer_class = StaffProfileSerializer

