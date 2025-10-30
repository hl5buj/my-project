# User ID만 제공하지 않고 더 많은 정보를 제공하려면 기존 클래스를
# 상속해서 만들면 된다.
# # serializer
# view
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User 정보를 직렬화하는 Serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT 토큰에 추가 사용자 정보를 포함하는 Serializer"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 토큰 페이로드에 사용자 정보 추가
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = "instructor"
        token['premium'] = True
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # 응답에 사용자 정보 추가
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserInfoView(APIView):
    """인증된 사용자 정보를 반환하는 View"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# www.mysite.com -> frontend
# www.mysite.com/api -> backend(192.168.1.100)
# www.mysite.com/llm -> llm backend (192.168.1.101)
