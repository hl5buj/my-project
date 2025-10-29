from django.urls import path
from .views import UserInfoView

urlpatterns = [
    path('me/', UserInfoView.as_view(), name='user_info'),
]