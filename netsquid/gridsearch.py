import numpy as np
from prept5 import avg_100_runs

NO_OF_BITS=24

# Define the grid search function
def grid_search(n_bits, distance_range, timeout_range, max_retries_range, accuracy_threshold=95):
    best_distance = None
    best_timeout = None
    best_max_retries = None
    best_accuracy = 0

    # Keep track of results in a dictionary for logging
    results = {}

    # Iterate over all combinations of distance, timeout, and max_retries
    for distance in distance_range:
        for timeout in timeout_range:
            for max_retries in max_retries_range:
                print(f"Testing with Distance={distance}, Timeout={timeout}, Max Retries={max_retries}")

                # Run the average function and get accuracy
                accuracy = avg_100_runs(n_bits, distance, timeout, max_retries)

                # Only keep configurations with accuracy above the threshold
                if accuracy >= accuracy_threshold:
                    # Store results for logging
                    results[(distance, timeout, max_retries)] = accuracy

                    # Update the best configuration if we find a better one
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
distance_range = np.arange(50, 501, 50)  # Distance from 50 to 500 in steps of 50 meters
timeout_range = np.logspace(10, 12, num=3)  # Timeout from 1e10 ns to 1e12 ns
max_retries_range = np.arange(5, 21, 5)  # Max retries from 5 to 20 in steps of 5

# Run the grid search
best_distance, best_timeout, best_max_retries, best_accuracy, results = grid_search(
    n_bits=NO_OF_BITS, 
    distance_range=distance_range, 
    timeout_range=timeout_range, 
    max_retries_range=max_retries_range,
    accuracy_threshold=95
)

# Optional: Print all results for comparison
print("\nAll tested configurations and their accuracy:")
for config, accuracy in results.items():
    print(f"Distance={config[0]}, Timeout={config[1]}, Max Retries={config[2]} -> Accuracy={accuracy}%")
