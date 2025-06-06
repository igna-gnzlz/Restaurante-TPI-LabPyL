from django.urls import path
from accounts_app.views import RegisterView, LoginView
from django.contrib.auth.views import LogoutView

app_name = 'accounts_app'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout')
]
