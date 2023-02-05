from django.urls import path

from .views import *

urlpatterns = [
    path('', WelcomeView.as_view(), name='welcome'),
    path('login/', LoginUser.as_view(), name='login'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('generate/', GenerateView.as_view(), name='generate'),
    path('questions/', QuestionsView.as_view(), name='questions'),
    path('content/<int:content_id>', ContentView.as_view(), name='content'),
    path('change/<int:content_id>', change_questions, name='change_questions'),

    #account
    path('account/', AccountView.as_view(), name='account'),
    path('logout/', logout_user, name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    #transaction
    path('complete-transation', completeTransation, name='completeTransation')

    #emails send
    # path('send-to-me/')
]