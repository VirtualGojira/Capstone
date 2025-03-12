import numpy as np
import csv
import matplotlib.pyplot as plt
from skopt import gp_minimize
from skopt.space import Real, Integer
from skopt.callbacks import DeltaYStopper
from prept5 import avg_100_runs

# Parameter ranges
PARAM_RANGES = {
    'distance': (1, 200),
    'timeout': (1, 1e9),
    'max_retries': (1, 10)
}

BIT_SIZES = [2**i for i in range(1, 9)]  # [2, 4, 8, ..., 256]

# Define search space
space = [
    Real(*PARAM_RANGES['distance'], name='distance', prior='log-uniform'),
    Real(*PARAM_RANGES['timeout'], name='timeout', prior='log-uniform'),
    Integer(*PARAM_RANGES['max_retries'], name='max_retries')
]

# Objective function
def objective(n_bits, **params):
    """Compute the objective function based on success count."""
    success_count = avg_100_runs(
        n_bits,
        float(params['distance']),
        float(params['timeout']),
        int(params['max_retries'])
    )
    return -params['distance'] if success_count >= 90 else -(params['distance'] * (success_count / 100))

# Wrapper function to pass parameters correctly
def objective_with_bits(params):
    return objective(n_bits, **dict(zip(['distance', 'timeout', 'max_retries'], params)))

# Function to write results to CSV
def write_results_to_csv(filename, results):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Bits", "Best Distance", "Best Timeout", "Best Max Retries", "Best Objective"])
        writer.writerows(results)

# Run optimization for each bit size
results = []
for n_bits in BIT_SIZES:
    print(f"\n=== Optimizing for {n_bits} bits ===")

    early_stop = DeltaYStopper(n_best=15, delta=0.01)

    print("Stage 1: Broad Exploration (100 iterations)")
    stage1_result = gp_minimize(
        func=objective_with_bits,
        dimensions=space,
        n_calls=100,
        n_initial_points=100,
        acq_func='gp_hedge',
        n_jobs=-1,
        callback=[early_stop],
        random_state=42,
        verbose=True
    )

    print("Stage 2: Focused Exploitation (50 iterations)")
    final_result = gp_minimize(
        func=objective_with_bits,
        dimensions=space,
        x0=stage1_result.x_iters,
        y0=stage1_result.func_vals,
        n_calls=50,
        acq_func='gp_hedge',
        n_jobs=-1,
        callback=[early_stop],
        random_state=42,
        verbose=True
    )

    best_distance, best_timeout, best_max_retries = final_result.x
    best_objective = -final_result.fun
    results.append([n_bits, best_distance, best_timeout, best_max_retries, best_objective])

    # Plot convergence
    plt.figure(figsize=(10, 5))
    all_calls = np.arange(1, len(stage1_result.func_vals) + len(final_result.func_vals) + 1)
    all_values = np.concatenate([stage1_result.func_vals, final_result.func_vals])
    plt.plot(all_calls, np.minimum.accumulate(all_values), label="Cumulative Minimum", linewidth=2)
    plt.axvline(x=len(stage1_result.func_vals), color='red', linestyle='--', label="Stage 1 → Stage 2")
    plt.xlabel("Number of Calls")
    plt.ylabel("Objective Value")
    plt.title(f"Convergence for {n_bits} Bits")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"convergence_{n_bits}bits.png", dpi=600)
    plt.close()

# Save results to CSV
write_results_to_csv("BO_algorithm_results.csv", results)
print("Results saved to genetic_algorithm_results.csv")
