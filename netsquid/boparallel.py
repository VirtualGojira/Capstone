from skopt import Optimizer
from skopt.space import Real, Integer
from skopt.utils import use_named_args
from skopt.callbacks import DeltaYStopper
from joblib import Parallel, delayed
import numpy as np
from prept5 import avg_100_runs

# Global variables and parameter ranges
NO_OF_BITS = 24
PARAM_RANGES = {
    'distance': (1, 200),
    'timeout': (1, 1e9),
    'max_retries': (1, 10)
}
space = [
    Real(*PARAM_RANGES['distance'], name='distance', prior='log-uniform'),
    Real(*PARAM_RANGES['timeout'], name='timeout', prior='log-uniform'),
    Integer(*PARAM_RANGES['max_retries'], name='max_retries')
]

# Objective function using named arguments
@use_named_args(space)
def objective(distance, timeout, max_retries):
    success_count = avg_100_runs(NO_OF_BITS, float(distance), float(timeout), int(max_retries))
    # For example, maximize success_count; here we minimize a negative score.
    return -distance if success_count >= 90 else -(distance * (success_count/100))

# Early stopping callback (if desired)
early_stop = DeltaYStopper(n_best=15, delta=0.01)

# Create the optimizer instance
optimizer = Optimizer(dimensions=space, random_state=42, acq_func='gp_hedge')

n_calls = 300
batch_size = 16  # Number of candidates to evaluate in parallel at each iteration
all_obj_values = []

# Loop using the ask-and-tell interface
for i in range(0, n_calls, batch_size):
    # Ask for a batch of candidate points
    candidates = [optimizer.ask() for _ in range(batch_size)]
    
    # Evaluate candidates in parallel using joblib
    results = Parallel(n_jobs=-1)(delayed(objective)(cand) for cand in candidates)

    
    # Tell the optimizer the results for each candidate
    for cand, res in zip(candidates, results):
        optimizer.tell(cand, res)
        all_obj_values.append(res)
    
    # Optional: check early stopping condition (if implemented)
    # if len(all_obj_values) > 15 and abs(np.min(all_obj_values[-15:]) - np.min(all_obj_values)) < 0.1:
    #     print("Early stopping criterion met.")
    #     break

# Final result is stored in the optimizer
best_index = np.argmin(optimizer.yi)
best_params = optimizer.Xi[best_index]
best_obj_value = optimizer.yi[best_index]
print("Best parameters:", best_params)
print("Best objective value:", best_obj_value)
