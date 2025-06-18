from django.urls import path
from django.contrib.auth.views import LogoutView
from accounts_app.views import UserNotificationDeleteView  # o la vista que vayas a usar
from accounts_app.views import UserNotificationDeleteAllView
from accounts_app.views import (
    UserRegisterView,
    UserLoginView,
    NotificationRecipientsView,
    UserNotificationsListView,
    UserNotificationDetailView,
    EditUsernameView,
    ProfileView,
)

app_name = 'accounts_app'

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('notification_recipients/<int:pk>/', NotificationRecipientsView.as_view(), name='notification_recipients'),
    path('my_notifications/', UserNotificationsListView.as_view(), name='user_notifications_list'),
    path('my_notifications/<int:pk>/', UserNotificationDetailView.as_view(), name='user_notification_detail'),
    path('profile/', ProfileView.as_view(), name='profile'),  # Usamos la vista basada en clase
    path('profile/edit-username/', EditUsernameView.as_view(), name='edit_username'),
     path('my_notifications/delete/<int:pk>/',UserNotificationDeleteView.as_view(),name='user_notification_delete'),
      path('my_notifications/delete_all/',UserNotificationDeleteAllView.as_view(),name='user_notification_delete_all'
    ),
]
