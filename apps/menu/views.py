from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def index(request):

    context = {
        "nome_pagina": "Página inicial",
    }

    return render(request, "menu/index.html", context)
