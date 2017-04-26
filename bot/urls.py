from django.conf.urls import url, include
from .views import lacbtView
urlpatterns = [
    url(r'^d09616f95f57d93877e960005c5b858e784b5416/?$', lacbtView.as_view()),
    
]