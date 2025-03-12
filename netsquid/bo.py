# Add these imports at the top
from skopt import gp_minimize
from skopt.space import Real, Integer
from skopt.utils import use_named_args
import numpy as np
from prept5 import avg_100_runs

NO_OF_BITS = 24

# Add parameter ranges at the beginning (after global variables)
PARAM_RANGES = {
    'distance': (1, 200),      # meters
    'timeout': (1, 1e9),      # ns
    'max_retries': (1, 10)       # retry attempts
}

# Add Bayesian optimization code at the end
if __name__ == "__main__":
    # Define search space
    space = [
        Real(*PARAM_RANGES['distance'], name='distance', prior='log-uniform'),
        Real(*PARAM_RANGES['timeout'], name='timeout', prior='log-uniform'),
        Integer(*PARAM_RANGES['max_retries'], name='max_retries')
    ]

    # Optimization objective
    @use_named_args(space)
    def objective(distance, timeout, max_retries):
        # Convert to integer values where needed
        max_retries = int(max_retries)
        distance = float(distance)
        timeout = float(timeout)
        
        # Run simulation
        success_count = avg_100_runs(
            NO_OF_BITS,
            distance=distance,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Composite objective: Maximize distance with success rate constraint
        if success_count >= 95:
            return -distance  # Negative because we minimize
        return -distance * (success_count / 100)  # Penalized objective

    # Run optimization
    result = gp_minimize(
        n_jobs=-1,
        func=objective,
        dimensions=space,
        n_calls=303,                # Total iterations
        n_random_starts=50,        # Random initial points
        acq_func='EI',             # Acquisition function
        noise=0.1,                 # Account for simulation noise
        random_state=42
    )

    # Print results
    print("\nOptimization results:")
    print(f"Best distance: {result.x[0]:.2f}m")
    print(f"Best timeout: {result.x[1]:.2e}ns")
    print(f"Best max_retries: {int(result.x[2])}")
    print(f"Best objective value: {-result.fun:.2f} (maximized distance)")
    
    # Verify with final run
    print("\nVerification run with best parameters:")
    final_count = avg_100_runs(
        NO_OF_BITS,
        distance=result.x[0],
        timeout=result.x[1],
        max_retries=int(result.x[2])
    )
    print(f"Final success rate: {final_count}/100")