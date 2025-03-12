import numpy as np
import concurrent.futures
from functools import partial
from prept5 import avg_100_runs

NO_OF_BITS=24

def grid_search_parallel(n_bits, distance_range, timeout_range, max_retries_range, accuracy_threshold=95):
    best_distance = None
    best_timeout = None
    best_max_retries = None
    best_accuracy = 0

    # Store results in a dictionary for logging
    results = {}

    # Helper function to evaluate each configuration
    def evaluate_config(distance, timeout, max_retries):
        print(f"Testing with Distance={distance}, Timeout={timeout}, Max Retries={max_retries}")
        accuracy = avg_100_runs(n_bits, distance, timeout, max_retries)
        
        # Only return the config if the accuracy is above the threshold
        if accuracy >= accuracy_threshold:
            return (distance, timeout, max_retries, accuracy)
        return None

    # Create a list of all configurations to test
    config_list = [(distance, timeout, max_retries) 
                   for distance in distance_range 
                   for timeout in timeout_range 
                   for max_retries in max_retries_range]

    # Use ThreadPoolExecutor or ProcessPoolExecutor to parallelize
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # We use partial to provide n_bits argument to the helper function
        results_future = list(executor.map(partial(evaluate_config, n_bits=n_bits), *zip(*config_list)))

    # Filter out any None results (those that didn't meet the accuracy threshold)
    valid_results = [result for result in results_future if result is not None]

    # Find the best result (maximizing distance and accuracy)
    for distance, timeout, max_retries, accuracy in valid_results:
        results[(distance, timeout, max_retries)] = accuracy
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_distance = distance
            best_timeout = timeout
            best_max_retries = max_retries

    # Print the best configuration found
    print("\nBest Configuration:")
    print(f"Distance: {best_distance}, Timeout: {best_timeout}, Max Retries: {best_max_retries}")
    print(f"Best Accuracy: {best_accuracy}%")

    # Return the best configuration and the corresponding accuracy
    return best_distance, best_timeout, best_max_retries, best_accuracy, results


# Set ranges for grid search
distance_range = np.arange(1, 200, 1)  # Distance from 50 to 500 in steps of 50 meters
timeout_range = np.arange(1, 1e9 + 1 - 100, 100)  # Timeout from 1e10 ns to 1e12 ns
max_retries_range = np.arange(1, 11, 1)  # Max retries from 5 to 20 in steps of 5

# Run the parallel grid search
best_distance, best_timeout, best_max_retries, best_accuracy, results = grid_search_parallel(
    n_bits=NO_OF_BITS, 
    distance_range=distance_range, 
    timeout_range=timeout_range, 
    max_retries_range=max_retries_range,
    accuracy_threshold=95
)

# Optional: Print all results for comparison
#print("\nAll tested configurations and their accuracy:")
#for config, accuracy in results.items():
#    print(f"Distance={config[0]}, Timeout={config[1]}, Max Retries={config[2]} -> Accuracy={accuracy}%")
