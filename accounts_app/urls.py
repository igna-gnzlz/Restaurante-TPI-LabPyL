from django.urls import path
from accounts_app.views import UserRegisterView, UserLoginView
from accounts_app.views import NotificationRecipientsView, UserNotificationsListView
from accounts_app.views import UserNotificationDetailView
from django.contrib.auth.views import LogoutView

app_name = 'accounts_app'

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('notification_recipients/<int:pk>/',
    NotificationRecipientsView.as_view(), name='notification_recipients'),
    path('my_notifications/',
    UserNotificationsListView.as_view(), name='user_notifications_list'),
    path('my_notifications/<int:pk>/',
    UserNotificationDetailView.as_view(), name='user_notification_detail')
]
