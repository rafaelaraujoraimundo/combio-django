from django.urls import path
from django.contrib.auth.decorators import permission_required

from dashboard.views import dashboard_ti, dashboard_controladoria


urlpatterns = [
    path('ti', dashboard_ti, name="dashboard_ti"),
    path('controladoria', dashboard_controladoria,
         name='dashboard_controladoria')
]