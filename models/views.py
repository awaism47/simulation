from .functionality import remove_numbers_from_string
from django.shortcuts import render
from .models import Process,Queue
from .simulation import run_and_plot_simulation
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
                'changeover': int(request.POST.get(f'changeover{i}')),
                'resource':int(request.POST.get(f'resource{i}'))
            }
            process_steps.append(step)
            print(process_steps)

        # Run simulation
        results, plot_base64 = run_and_plot_simulation(simulation_time, warm_up_time, inter_arrival_time, process_steps)
        # Pass results and the plot to the template
        context = {
            'results': results,
            'plot_base64': plot_base64
        }
        return render(request, 'models/results.html', context)

    return render(request, 'models/index.html')

@csrf_exempt
def api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
         # Extract environment settings
        env_data = data['environment']
        simulation_time = int(env_data['Simulation_time'])
        warm_up_time = int(env_data['warm_up_time'])
        inter_arrival_time = int(env_data['interarrival'])

        #
        # Process the steps
        process_steps = []
        process_data = data['process']
        for step_value in process_data:
            if isinstance(step_value, dict):
                # If its a dict then just add it 
                process_step = process_individual_step(step_value)
                process_steps.append(process_step)
            elif isinstance(step_value, list):

                #if its a list then first create an aggregated step
                aggregated_step = {}
                  
                # then process a list of steps
                for step in step_value:
                        processed_step=process_individual_step(step)
                        
                        # Initialize an aggregated step dictionary
                        if(len(aggregated_step)==0):
                            aggregated_step = processed_step
                        else:
                            # Aggregate resources for similar steps
                            aggregated_step['resource'] += processed_step['resource']

                process_steps.append(aggregated_step)
        print(process_steps, simulation_time)
        # Run simulation
        avg_waiting_time, avg_lead_time, throughput, plot_base64 = run_and_plot_simulation(simulation_time, warm_up_time, inter_arrival_time, process_steps)

        # Prepare and send JSON response
        response_data = {
            'average_waiting_time': avg_waiting_time,
            'average_lead_time':avg_lead_time,
            'average_throughput':throughput,
            'plot_base64': plot_base64  # Uncomment if you want to send the plot as well
        }
        return JsonResponse(response_data)

    return render(request, 'models/index.html')

def process_individual_step(step):
    step_name = remove_numbers_from_string(step['name'])
    if step.get('type') == 'queue':
        return {
            'type': 'queue',
            'name': step_name,
            'resource': int(step.get('capacity', 0)),
            'initial_amount': int(step.get('initial', 0))
        }
    else:
        return {
            'type': 'process',
            'name': step_name,
            'cycle_time': int(step.get('cycle_time', 0)),
            'distribution': step.get('distribution', ""),
            'min_value': int(step.get('min_value', 0)) if 'min_value' in step else 0,
            'max_value': int(step.get('max_value', 0)) if 'max_value' in step else 0,
            'mean_value': int(step.get('mean_value', 0)) if 'mean_value' in step else 0,
            'std_dev': int(step.get('std_dev', 0)) if 'std_dev' in step else 0,
            'changeover': int(step.get('changeover', 0)),
            'resource': int(step.get('resource', 0))
        }

