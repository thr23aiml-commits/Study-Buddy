from django.urls import path
from .import views
urlpatterns = [
    path('', views.home,name="home"),
    path('quiz/', views.quiz,name="quiz"),
    path('summary/',views.summarizer,name="summarizer"),
    path('generate-quiz/', views.generate_quiz_view, name='generate_quiz'),
    path('summarize-paragraph/', views.summarize_paragraph_view, name='summarize_paragraph'),
]
