from django.shortcuts import render, redirect, get_object_or_404
from .relational_cirle import analyse
import os
from django.conf import settings as conf_settings


def index(request):
    file = open(os.path.join(conf_settings.BASE_DIR, 'test_data.csv'))
    ana = analyse(file, 400, 400)
    return render(request, 'twitter_network/index.html', {'ana': ana})
