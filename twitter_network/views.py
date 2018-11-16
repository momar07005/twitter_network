from django.shortcuts import render, redirect, get_object_or_404
from .models import *
import os
from django.conf import settings as conf_settings

from .relational_cirle import analyse
#from .twitter_process_data import get_data


def index(request):
    file = open(os.path.join(conf_settings.BASE_DIR, 'test_data.csv'))
    ana = analyse(file, 1000, 700)
    ana = list(ana)
    plot_list = []
    id = 0
    for plot in ana:
        id += 1
        plot_list.append((id, plot))

    return render(request, 'twitter_network/index.html', {'plot_list': plot_list, 'n': range(1, len(ana))})




		

