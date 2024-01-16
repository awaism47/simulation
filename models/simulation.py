import simpy
import random
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for matplotlib
import matplotlib.pyplot as plt
import io
import base64

class ManufacturingSimulation:
    def __init__(self, env, simulation_time, warm_up_time, process_steps, inter_arrival_time):
        self.env = env
        self.simulation_time = simulation_time
        self.warm_up_time = warm_up_time
        self.process_steps = process_steps
        self.inter_arrival_time = inter_arrival_time  # New parameter for inter-arrival time
        self.results = []
        self.waiting_times = []  # Initialize the waiting times list
        self.throughput_times = [] 
        self.waiting_times_per_process = {step['name']: [] for step in process_steps}

    def setup(self):
        resources = {step['name']: simpy.Resource(self.env, capacity=1) for step in self.process_steps}
        self.env.process(self.item_generator(resources))

    def create_process(self, item_number,item_name, step, resource):
        cycle_time = calculate_cycle_time(step)

        def process(env):
            request_start = env.now
            with resource.request() as req:
                yield req
                wait = env.now - request_start
                print(wait)
                self.waiting_times.append(wait)  # Record waiting time

                start_time = env.now
                yield env.timeout(cycle_time)
                completion_time = env.now
                self.throughput_times.append(completion_time - start_time)  # Record throughput time


                if env.now >= self.warm_up_time:
                    self.results.append({
                        'item_number': item_number,
                        'item_name': item_name,
                        'process_name': step['name'],
                        'start_time': start_time,
                        'waiting_time':wait,
                        'completion_time': completion_time
                    })
                    self.waiting_times_per_process[step['name']].append(wait) 

            yield env.timeout(step['changeover'])

        return process

    def item_generator(self, resources):
        item_number = 1
        while True:
            yield self.env.timeout(self.inter_arrival_time)
            item_name = f"Item_{item_number}"
            for step in self.process_steps:
                process_generator = self.create_process(item_number, item_name, step, resources[step['name']])(self.env)
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
        return self.results

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
        process_steps = [step['name'] for step in self.process_steps]
        part_numbers = sorted(set([result['item_number'] for result in self.results]))
        bottom_values = [0] * len(part_numbers)

        for step in process_steps:
            step_waiting_times = [self.calculate_waiting_time_for_step(step, part) for part in part_numbers]
            plt.bar(part_numbers, step_waiting_times, bottom=bottom_values, label=step)
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

def run_and_plot_simulation(simulation_time, warm_up_time, inter_arrival_time, process_steps):
    env = simpy.Environment()
    simulation = ManufacturingSimulation(env, simulation_time, warm_up_time, process_steps, inter_arrival_time)
    results = simulation.run()
    plot_base64 = simulation.plot_results() 
    return results, plot_base64
