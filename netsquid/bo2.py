# Add these imports at the top
from skopt import gp_minimize
from skopt.space import Real, Integer
from skopt.utils import use_named_args
from skopt.callbacks import DeltaYStopper
from skopt.plots import plot_convergence
import matplotlib.pyplot as plt
import numpy as np
from prept5 import avg_100_runs

NO_OF_BITS = 24

# Parameter ranges (add after global variables)
PARAM_RANGES = {
    'distance': (1, 200),    # Extended to 20km
    'timeout': (1, 1e9),     # Wider timeout range
    'max_retries': (1, 10)     # Increased retry attempts
}

# Add this function to write results to a file
def write_results_to_file(filename, stage1_result, final_result):
    with open(filename, 'w') as f:
        # Write header
        f.write("=== Optimization Results ===\n\n")
        
        # Write stage 1 summary
        f.write("Stage 1: Broad Exploration\n")
        f.write(f"  Iterations: {len(stage1_result.func_vals)}\n")
        f.write(f"  Best Objective: {-stage1_result.fun:.2f}\n")
        f.write(f"  Best Parameters:\n")
        f.write(f"    Distance: {stage1_result.x[0]:.2f}m\n")
        f.write(f"    Timeout: {stage1_result.x[1]:.2e}ns\n")
        f.write(f"    Max Retries: {int(stage1_result.x[2])}\n\n")
        
        # Write stage 2 summary
        f.write("Stage 2: Focused Exploitation\n")
        f.write(f"  Iterations: {len(final_result.func_vals)}\n")
        f.write(f"  Best Objective: {-final_result.fun:.2f}\n")
        f.write(f"  Best Parameters:\n")
        f.write(f"    Distance: {final_result.x[0]:.2f}m\n")
        f.write(f"    Timeout: {final_result.x[1]:.2e}ns\n")
        f.write(f"    Max Retries: {int(final_result.x[2])}\n\n")
        
        # Write convergence details
        f.write("=== Convergence Details ===\n")
        f.write(f"  Total Iterations: {len(stage1_result.func_vals) + len(final_result.func_vals)}\n")
        f.write(f"  Final Objective: {-final_result.fun:.2f}\n")
        f.write(f"  Optimal Distance: {final_result.x[0]:.2f}m\n")
        f.write(f"  Optimal Timeout: {final_result.x[1]:.2e}ns\n")
        f.write(f"  Optimal Max Retries: {int(final_result.x[2])}\n")

# Add optimization code at the end
if __name__ == "__main__":
    # Define search space
    space = [
        Real(*PARAM_RANGES['distance'], name='distance', prior='log-uniform'),
        Real(*PARAM_RANGES['timeout'], name='timeout', prior='log-uniform'),
        Integer(*PARAM_RANGES['max_retries'], name='max_retries')
    ]

    # Objective function
    @use_named_args(space)
    def objective(distance, timeout, max_retries):
        success_count = avg_100_runs(
            NO_OF_BITS,
            distance=float(distance),
            timeout=float(timeout),
            max_retries=int(max_retries)
        )
        return -distance if success_count >= 90 else -(distance * (success_count/100))

    # Early stopping callback
    early_stop = DeltaYStopper(
        n_best=15,    # Check last 15 iterations
        delta=0.01    # Stop if improvement < 1%
    )

    # Multi-stage optimization with increased iterations
    print("=== Stage 1: Broad Exploration (100 iterations) ===")
    stage1_result = gp_minimize(
        func=objective,
        dimensions=space,
        n_calls=100,
        n_initial_points=100,
        acq_func='gp_hedge',
        n_jobs=-1,
        callback=[early_stop],
        random_state=42,
        verbose=True
    )

    print("\n=== Stage 2: Focused Exploitation (50 iterations) ===")
    final_result = gp_minimize(
        func=objective,
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

    # Generate convergence plot manually
    plt.figure(figsize=(12, 6))

    # Combine results from both stages
    all_calls = np.arange(1, len(stage1_result.func_vals) + len(final_result.func_vals) + 1)
    all_values = np.concatenate([stage1_result.func_vals, final_result.func_vals])

    # Plot cumulative minimum
    cumulative_min = np.minimum.accumulate(all_values)
    plt.plot(all_calls, cumulative_min, label="Cumulative Minimum", linewidth=2)

    # Add stage separation line
    stage_split = len(stage1_result.func_vals)
    plt.axvline(x=stage_split, color='red', linestyle='--', label="Stage 1 → Stage 2")

    # Annotate stages
    plt.text(stage_split / 2, max(cumulative_min) * 0.9, "Stage 1: Exploration", ha='center', fontsize=12)
    plt.text(stage_split + (len(final_result.func_vals) / 2), max(cumulative_min) * 0.9, "Stage 2: Exploitation", ha='center', fontsize=12)

    # Add labels and title
    plt.xlabel("Number of Calls (n)", fontsize=12)
    plt.ylabel("Objective Value (min(f(x)))", fontsize=12)
    plt.title("Optimization Convergence with Early Stopping", fontsize=14)
    plt.legend()
    plt.grid(True)

    # Save and show the plot
    plt.savefig("convergence.png", dpi=600)
    plt.show()
    # Add this after generating the convergence plot
    write_results_to_file("optimization_results.txt", stage1_result, final_result)
    print("Results saved to optimization_results.txt") 