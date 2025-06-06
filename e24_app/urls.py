from django.urls import path
from . import views

urlpatterns = [
    path('', views.live_results, name='live_results'),
    path('live-results/', views.live_results, name='live_results'),
    #path('save-inputs/', views.save_human_inputs, name='save_inputs'),
    path('save-predictions/', views.save_predictions, name='save_predictions'),
    path('load-predictions/', views.load_predictions, name='load_predictions'),
]

