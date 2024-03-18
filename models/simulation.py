import simpy
import random
import matplotlib
import matplotlib.pyplot as plt
import io
import base64
matplotlib.use('Agg')  # Use non-interactive backend for matplotlib


class ManufacturingSimulation:

    def __init__(self, env, simulation_time, warm_up_time,
                 process_steps, inter_arrival_time):
        self.env = env
        self.simulation_time = simulation_time
        self.warm_up_time = warm_up_time
        self.process_steps = process_steps
        self.inter_arrival_time = inter_arrival_time
        self.results = []
        self.waiting_times = []
        self.throughput_times = []
        self.waiting_times_per_process = {step['name']: []
                                          for step in process_steps}
        self.simpy_objects = {}

    def setup(self):
        self.resources = {}
        for step_data in self.process_steps:
            step_key = step_data['name']
            # need to fix this
            if step_data['type']=='queue':
                # for containers
                self.resources[step_key] = simpy.Container(
                    self.env, capacity=step_data['resource'],
                    init=step_data['initial_amount'])
            else:
                # For resource
                self.resources[step_key] = simpy.Resource(self.env, capacity=step_data['resource'])

            print(f"Resource '{step_key}' has a capacity of {self.resources[step_key].capacity}")

        self.env.process(self.item_generator(self.resources))

    def create_process(self, item_number, item_name, step_key, step_data, resource):
        cycle_time = calculate_cycle_time(step_data)
        current_step_index = self.process_steps.index(step_data)
        next_step = self.process_steps[
            current_step_index + 1] if current_step_index + 1 < len(
                self.process_steps) else None
        print(f'next step is {next_step}')

        def process(env):

            request_start = env.now
            # Handle if current step is a queue
            if step_data['type'] == 'queue':
                yield resource.get(1)  # Get an item from the container

            # Handle processing with the resource
            start_time = 0
            wait = 0
            completion_time = 0
            if step_data['type'] == 'process':
                with resource.request() as req:
                    yield req
                    wait = env.now - request_start
                    self.waiting_times.append(wait)  # Record waiting time
                    start_time = env.now
                    yield env.timeout(cycle_time)
                    completion_time = env.now
                    self.throughput_times.append(completion_time - start_time)  # Record throughput time

            # Record results
            if env.now >= self.warm_up_time:
                self.results.append({
                    'item_number': item_number,
                    'item_name': item_name,
                    'process_name': step_data['name'],
                    'start_time': start_time,
                    'waiting_time': wait,
                    'completion_time': completion_time
                    })
                self.waiting_times_per_process[step_key].append(wait)
                    
            # Handle if next step is a queue
            if next_step and next_step['type'] == 'queue':
                next_step_object = self.simpy_objects.get(next_step['name'])
                if next_step_object:
                    yield next_step_object.put(1)  # Put an item into the next container
        return process

    def item_generator(self, resources):
        item_number = 1
        while True:
            yield self.env.timeout(self.inter_arrival_time)
            item_name = f"Item_{item_number}"
            for step_data in self.process_steps:
                step_key=step_data['name']
                #need to fix this
                process_generator = self.create_process(item_number, item_name, step_key, step_data, resources[step_key])(self.env)
                self.env.process(process_generator)
            item_number += 1
    def calculate_waiting_time_for_step(self, step_name, item_number):
        # This is a placeholder implementation.
        # You need to adapt this method based on how you're tracking waiting times.
        # Example logic (assuming waiting times are stored in a specific way):
        total_waiting_time = 0
        for result in self.results:
            if result['item_number'] == item_number and result['process_name'] == step_name:
                total_waiting_time += result['waiting_time']
        return total_waiting_time

    def run(self):
        self.setup()
        self.env.run(until=self.simulation_time)
        # Calculate average waiting time
        avg_waiting_time = int(sum(self.waiting_times) / len(self.waiting_times)) if self.waiting_times else 0
        # Calculate lead times and average lead time
        lead_times = [result['completion_time'] - result['start_time'] for result in self.results]
        avg_lead_time = int(sum(lead_times) / len(lead_times)) if lead_times else 0
        # Calculate throughput (number of completed parts / total simulation time)
        total_parts_completed = len(set(result['item_number'] for result in self.results))
        throughput = int((total_parts_completed / (self.simulation_time - self.warm_up_time))*60*60)
        return self.results, avg_waiting_time, avg_lead_time, throughput

    def plot_results(self):
        plt.figure(figsize=(18, 6))

        plt.subplot(1, 3, 1)
        plt.plot(self.waiting_times, label='Waiting Time')
        plt.title('Waiting Time over Simulation')
        plt.xlabel('Event')
        plt.ylabel('Time')

        # Plot for average waiting time per process
        plt.subplot(1, 3, 2)
        process_names = list(self.waiting_times_per_process.keys())
        avg_waiting_times = [sum(times)/len(times) if times else 0 for times in self.waiting_times_per_process.values()]
        plt.bar(process_names, avg_waiting_times)
        plt.title('Average Waiting Time per Process')
        plt.xlabel('Process')
        plt.ylabel('Average Waiting Time')

        # Plot for visualization of waiting times per part at each process step
        plt.subplot(1, 3, 3)
        part_numbers = sorted(set([result['item_number'] for result in self.results]))
        bottom_values = [0] * len(part_numbers)

        for step_name in process_names:
            step_waiting_times = [self.calculate_waiting_time_for_step(step_name, part) for part in part_numbers]
            plt.bar(part_numbers, step_waiting_times, bottom=bottom_values, label=step_name)
            bottom_values = [bottom + wait for bottom, wait in zip(bottom_values, step_waiting_times)]

        plt.title('Waiting Time per Part at Each Step')
        plt.xlabel('Part Item Number')
        plt.ylabel('Waiting Time')
        plt.legend()

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()     
        return image_base64


def calculate_cycle_time(step):
    distribution = step.get('distribution', 'fixed')
    if distribution == 'uniform':
        return random.uniform(step.get('min_value', 5), step.get('max_value', 15))
    elif distribution == 'exponential':
        return random.expovariate(1.0 / step.get('mean_value', 8))
    elif distribution == 'normal':
        return max(0, random.normalvariate(step.get('mean_value', 10), step.get('std_dev', 2)))
    else:
        return step.get('cycle_time', 10)  # Default fixed cycle time


def run_and_plot_simulation(simulation_time, warm_up_time,
                            inter_arrival_time, process_steps):
    env = simpy.Environment()
    simulation = ManufacturingSimulation(
        env, simulation_time, warm_up_time, process_steps, inter_arrival_time)
    results, avg_waiting_time, avg_lead_time, throughput = simulation.run()
    plot_base64 = simulation.plot_results()
    return results, avg_waiting_time, avg_lead_time, throughput, plot_base64
