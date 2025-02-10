from django.urls import path
from . import views

urlpatterns = [
    path('', views.getRoutes),

    path('schedule/', views.getSchedule),
    path('schedule/parameters/', views.getScheduleParameters),
    path('schedule/parameters/<str:pk>/', views.getScheduleParametersSpecific),
    path('schedule/version/', views.getScheduleVersion),
    path('schedule/current/<str:pk>/', views.getScheduleCurrent),
    path('schedule/base/<str:pk1>/<str:pk2>/', views.getScheduleBase),
    path('schedule/parameters/<str:pk>/upload/', views.uploadScheduleParameters),
    path('schedule/current/stagepair/<str:pk1>/<str:pk2>/', views.stageCurrentSchedulePair),
    path('schedule/current/applybase/<str:pk1>/<str:pk2>/<str:pk3>/', views.applyBaseScheduleToCurrent),
    path('schedule/base/stagepair/<str:pk1>/<str:pk2>/<str:pk3>/', views.stageBaseSchedulePair),
    path('schedule/base/stageschedule/', views.stageBaseScheduleName),
    path('schedule/current/apply/<str:pk1>/<str:pk2>/', views.applyCurrentScheduleChanges),
    path('schedule/base/apply/<str:pk1>/<str:pk2>/', views.applyBaseScheduleChanges),
    path('schedule/current/reset/<str:pk>/', views.resetCurrentScheduleChanges),
    path('schedule/base/reset/<str:pk1>/<str:pk2>/', views.resetBaseScheduleChanges),
]