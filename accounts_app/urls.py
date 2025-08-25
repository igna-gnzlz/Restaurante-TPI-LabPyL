from django.urls import path
from django.contrib.auth.views import LogoutView
from accounts_app.views import (
    UserRegisterView,
    UserLoginView,
    NotificationRecipientsView,
    UserNotificationsListView,
    DeleteNotificationView,
    DeleteAllNotificationsView,
    UserNotificationDetailView,
    EditUsernameView,
    ProfileView,
    MarkNotificationReadView
)
from . import views

app_name = 'accounts_app'

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('notification_recipients/<int:pk>/', NotificationRecipientsView.as_view(), name='notification_recipients'),
    path('my_notifications/', UserNotificationsListView.as_view(), name='user_notifications_list'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit-username/', EditUsernameView.as_view(), name='edit_username'),

    path('delete_notification/<int:pk>/', DeleteNotificationView.as_view(), name='ajax_delete_notification'),
    path('delete_all_notifications/', DeleteAllNotificationsView.as_view(), name='ajax_delete_all_notifications'),
    path('my_notifications/<int:pk>/', UserNotificationDetailView.as_view(), name='user_notification_detail'),
    path('notifications/mark-read/<int:pk>/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
]
