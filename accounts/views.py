from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from rest_framework import generics, permissions
from rest_framework import status
from .models import User, PasswordHistory
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
    EnhancedChangePasswordSerializer,
)
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import IsAuthenticated

class UsersListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            try:
                user = User.objects.get(id=pk)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)
        else:
            user = request.user

        serializer = UserSerializer(user)
        return Response(serializer.data)
     
    def put(self, request, pk=None):
        user = User.objects.get(id=pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
    def delete(self, request, pk):
        user = User.objects.get(id=pk)
        user.delete()
        return Response('user removed successfuly!')
        
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class TokenRefreshView(TokenRefreshView):
    pass


class RegisterUserView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=400)

        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=400)

        if not user.is_active:
            return Response({"error": "Account disabled"}, status=403)

        login(request, user)
        refresh = RefreshToken.for_user(user)

        profile_picture = (
            request.build_absolute_uri(user.profile_picture.url)
            if user.profile_picture
            else None
        )

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "id": user.id,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "profile_picture": profile_picture,
        })


class LogoutUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({"success": "Logged out successfully"})

class EnhancedChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = EnhancedChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            
            # Check current password
            if not user.check_password(serializer.validated_data['current_password']):
                return Response(
                    {'error': 'Current password is incorrect.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            new_password = serializer.validated_data['new_password']
            
            # Check password history (prevent reusing recent passwords)
            if self.is_password_in_history(user, new_password):
                return Response(
                    {'error': 'You cannot reuse a recently used password.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Save to password history
            self.save_password_history(user, new_password)
            
            # Update session auth hash to keep user logged in
            update_session_auth_hash(request, user)
            
            # Log the password change (optional)
            self.log_password_change(user, request)
            
            return Response(
                {
                    'message': 'Password changed successfully.',
                    'timestamp': timezone.now().isoformat()
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def is_password_in_history(self, user, new_password):
        """
        Check if the new password was used in the last 6 months
        """
        six_months_ago = timezone.now() - timedelta(days=180)
        
        recent_passwords = PasswordHistory.objects.filter(
            user=user,
            created_at__gte=six_months_ago
        )
        
        for password_history in recent_passwords:
            if password_history.check_password(new_password):
                return True
        
        return False
    
    def save_password_history(self, user, password):
        """
        Save the new password to history
        """
        PasswordHistory.objects.create(user=user, password=password)
        
        # Keep only last 10 passwords
        passwords_to_keep = PasswordHistory.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        
        PasswordHistory.objects.filter(user=user).exclude(
            id__in=passwords_to_keep.values_list('id', flat=True)
        ).delete()
    
    def log_password_change(self, user, request):
        """
        Log password change activity
        """
        # You can integrate with your logging system here
        print(f"Password changed for user: {user.username} at {timezone.now()}")
        # Or use Django's logging
        import logging
        logger = logging.getLogger('security')
        logger.info(f"Password changed for user: {user.username}", extra={
            'user_id': user.id,
            'ip_address': self.get_client_ip(request)
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    