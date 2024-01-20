from django.urls import path
from . import views

urlpatterns=[
    path("",views.home,name="home"),
    path("models",views.index,name="index"),
    path("simulation",views.run_simulation,name="run"),
    path("api",views.api,name="api"),
]