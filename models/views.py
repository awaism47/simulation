from django.http import HttpResponse
from django.shortcuts import render
from .models import Process,Queue
from .simulation import run_and_plot_simulation
import simpy




def index(request):

    return render(request, "models/index.html")

def home(request):

    return render(request, "models/home.html")

def run_simulation(request):
    if request.method == 'POST':
        simulation_time = int(request.POST.get('simulation_time'))
        warm_up_time = int(request.POST.get('warm_up_time'))
        inter_arrival_time = int(request.POST.get('inter_arrival_time'))
        step_count = int(request.POST.get('step_count'))

        process_steps = []
        for i in range(1, step_count + 1):
            step = {
                'name': request.POST.get(f'name{i}'),
                'distribution': request.POST.get(f'cycleTimeDistribution{i}'),
                'cycle_time': int(request.POST.get(f'cycleTime{i}')),  # Adjust based on distribution
                'changeover': int(request.POST.get(f'changeover{i}'))
            }
            process_steps.append(step)

        # Run simulation
        results, plot_base64 = run_and_plot_simulation(simulation_time, warm_up_time, inter_arrival_time, process_steps)
        # Pass results and the plot to the template
        context = {
            'results': results,
            'plot_base64': plot_base64
        }
        return render(request, 'models/results.html', context)

    return render(request, 'models/index.html')

