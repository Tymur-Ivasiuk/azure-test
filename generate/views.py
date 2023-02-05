import json
import os

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView, CreateView, DetailView
from django.forms.models import model_to_dict

from generate.forms import *
from generate.models import *
from generate.utils import *


class WelcomeView(TemplateView):
    template_name = 'generate/welcome.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Welcome'

        return context


class LoginUser(LoginView):
    template_name = 'generate/login.html'
    form_class = LoginUserForm

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('generate')
        return super(LoginUser, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context

    def form_valid(self, form):
        if not self.request.POST.get('remember', None):
            self.request.session.set_expiry(0)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('generate')

def logout_user(request):
    logout(request)
    return redirect('welcome')


class RegisterUser(CreateView):
    template_name = 'generate/register.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Register'

        return context


class GenerateView(FormView):
    template_name = 'generate/generate.html'
    form_class = GenerateForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return super(GenerateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Generate'

        context['poem_styles'] = PoemStyles.objects.all()
        context['letter_styles'] = LetterStyles.objects.all()
        context['tone'] = Tone.objects.all()
        context['occasion'] = Occasion.objects.all()
        context['relationship_types'] = RelationshipTypes.objects.all()

        d = CreditsBuyPriceAndCount.objects.last()
        context['credits_buy'] = d if d else {'credits_count': 50, 'price': 2.00}

        context['archive'] = Content.objects.filter(user=self.request.user)[:5]

        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            if (request.POST.get('occasion') and request.POST.get('tone') and
                    request.POST.get('genders') and request.POST.get('relationship_type')):
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        d = {'Letter': 'letter', 'Poem': 'poem', 'Note': 'note'}
        if self.request.user.profile.credits_count < CreditsPrice.objects.filter(
                credits_type=d.get(self.request.POST.get('type'))).first().credits:
            messages.error(self.request, "Sorry, you don't have enough credits")
            return redirect('generate')
        else:
            self.request.session['generate_info'] = {k: v for k, v in self.request.POST.items() if
                                                     k not in {'csrfmiddlewaretoken'}}
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please, provide data before submitting the form.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('questions')


class QuestionsView(TemplateView):
    template_name = 'generate/questions.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('login')
        if not request.session.get('generate_info'):
            return redirect('generate')
        return super(QuestionsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Questions'

        context['questions'] = Questions.objects.all().prefetch_related('answers_set')
        context['saved_answers'] = self.request.user.profile.save_answers.get('answers', [])
        print(context['saved_answers'])
        return context

    def post(self, request, *args, **kwargs):
        print(request.POST)
        if request.POST.get('save'):
            answers = []
            for i in dict(request.POST).items():
                try:
                    int(i[0])
                    answers += i[1]
                except:
                    pass
            request.user.profile.save_answers = {'answers': answers}
            request.user.profile.save()
            messages.success(request, 'Your checkbox answers have been saved')
            return redirect('generate')
        else:
            dict_answers = {k: v for k, v in dict(self.request.POST).items() if k not in {'csrfmiddlewaretoken'}}
            ss = send_ai_request(request.session.get('generate_info'),
                                 dict_answers,
                                 request.user)
            return redirect(ss)



class ContentView(DetailView):
    model = Content
    template_name = 'generate/content.html'
    pk_url_kwarg = 'content_id'
    context_object_name = 'content'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return super(ContentView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = context['content'].title
        context['length'] = Length.objects.all()
        context['answers_count'] = len(context['content'].answers.keys())
        context['questions_count'] = Questions.objects.all().count()

        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('length'):
            print(request.POST)
            if self.request.user.profile.credits_count < CreditsPrice.objects.filter(
                    credits_type=request.POST.get('content_type')).first().credits:
                messages.error(request, "Sorry, you don't have enough credits")
                return redirect('generate')

            self.request.session['generate_info']['length'] = request.POST.get('length')
            ss = send_ai_request(request.session.get('generate_info'),
                                 Content.objects.get(id=kwargs['content_id']).answers,
                                 request.user)
            return redirect(ss)

        return redirect(request.path)


def change_questions(request, content_id):
    content = Content.objects.get(id=content_id)

    if request.user.profile.credits_count < CreditsPrice.objects.filter(
            credits_type=content.content_type).first().credits:
        messages.error(request, "Sorry, you don't have enough credits")
        return redirect('generate')
    else:
        request.session['generate_info'] = content.content_info

    return redirect('questions')


def completeTransation(request):
    body = json.loads(request.body)
    request.user.profile.credits_count += body.get('credits', 0)
    request.user.profile.save()

    Transactions.objects.create(
        user=request.user,
        credits_count=body.get('credits', 0),
        price=body.get('price', 0)
    )
    return JsonResponse({'credits': request.user.profile.credits_count})


class AccountView(TemplateView):
    template_name = 'generate/account.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return super(AccountView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Account'
        user_dict = model_to_dict(self.request.user)
        profile_dict = model_to_dict(self.request.user.profile)

        info = {**user_dict, **profile_dict}
        d = {}
        for i in info:
            if i in ['first_name', 'last_name', 'email', 'phone_number', 'partner_email', 'partner_phone_number']:
                d[i] = info[i]

        context['form'] = AccountForm(d)
        context['archive'] = Content.objects.filter(user=self.request.user)[:5]

        d = CreditsBuyPriceAndCount.objects.last()
        context['credits_buy'] = d if d else {'credits_count': 50, 'price': 2.00}

        return context

class ChangePasswordView(FormView):
    template_name = 'generate/change_password.html'
    form_class = ChangePasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Change Password'

        return context

    def get_form_kwargs(self):
        kwargs = super(ChangePasswordView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_success_url(self):
        return reverse_lazy('account')
