from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('view/<str:comp_key>/', views.view_component, name='view_component'),
]
