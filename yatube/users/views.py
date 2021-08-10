from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm
from django.views.generic.base import TemplateView


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('login')
    template_name = "signup.html"


class JustStaticPage(TemplateView):
    template_name = 'app_name/just_page.html'
