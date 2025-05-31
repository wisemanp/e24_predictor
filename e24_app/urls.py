from django.urls import path
from . import views

urlpatterns = [
    path('', views.input_team, name='set_team_id'),
    path('live-results/', views.live_results, name='live_results'),
    #path('save-inputs/', views.save_human_inputs, name='save_inputs'),
    path('save-predictions/', views.save_predictions, name='save_predictions'),
]

