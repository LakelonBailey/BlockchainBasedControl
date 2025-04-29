from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponse
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login
from central_server.settings import AUTHENTICATION_BACKEND_MAP


class LoginView(View):
    def get(self, request: HttpRequest):
        if request.user.is_authenticated:
            return redirect("/admin/")
        next = request.GET.get("next", None)
        context = {}
        if next:
            context["next"] = next

        return render(request, "registration/login.html", context)

    def post(self, request: HttpRequest):
        data = request.POST.dict()
        try:
            email = data["email"]
            password = data["password"]
            next = data.get("next", "/admin/")
        except KeyError:
            return HttpResponseBadRequest()

        user = User.objects.filter(username__iexact=email).first()
        if user is None or not user.check_password(password):
            context = {
                "email": email,
                "error": "Invalid Credentials",
            }
            return render(request, "registration/login.html", context)
        else:
            login(request, user, backend=AUTHENTICATION_BACKEND_MAP["oauth"])

        if next:
            return redirect(next)

        return HttpResponse("Logged in!")


class SignupView(View):
    def get(self, request: HttpRequest):
        if request.user.is_authenticated:
            return redirect("/admin/")
        next = request.GET.get("next", None)
        context = {}
        if next:
            context["next"] = next

        return render(request, "registration/signup.html", context)

    def post(self, request: HttpRequest):
        data = request.POST.dict()
        try:
            first_name = data["first_name"]
            last_name = data["last_name"]
            email = data["email"]
            password = data["password"]
            confirm_password = data["confirm_password"]
            next = data.get("next", "/admin/")
        except KeyError:
            return HttpResponseBadRequest()

        error = None
        user = None
        if len(password) < 10:
            error = "Password must be at least 10 characters"
        elif password != confirm_password:
            error = "Passwords do not match"
        else:
            try:
                user = User(
                    username=email.lower(),
                )
                user.set_password(password)
                user.save()
            except IntegrityError as e:
                print(e)
                if "unique constraint" in str(e):
                    error = "That email is taken"
                else:
                    error = "We experienced an error"
        if error:
            context = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "error": error,
            }
            return render(request, "registration/signup.html", context)

        login(request, user)

        if next:
            return redirect(next)

        return HttpResponse("Account created!")
