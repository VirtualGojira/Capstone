import gym
from gym import spaces
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import DummyVecEnv
from prept5 import avg_100_runs

NO_OF_BITS = 24  # From original code

class BB84Env(gym.Env):
    def __init__(self):
        super(BB84Env, self).__init__()
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(3,), dtype=np.float32)
        
        # Initialize state variables with realistic starting values
        self.current_distance = 50.0  # Start with moderate distance
        self.current_timeout = 1e6    # Initial timeout 1ms (1e6 ns)
        self.current_retries = 3      # Moderate retry count

    def _normalize_state(self):
        """Normalize state parameters to [0,1] range"""
        return np.array([
            (self.current_distance - 1) / 199,
            (self.current_timeout - 1e4) / (1e9 - 1e4),
            (self.current_retries - 1) / 9
        ], dtype=np.float32)

    def reset(self):
        # Reset to initial values with small random variations
        self.current_distance = np.clip(50 + np.random.randint(-10, 10), 1, 200)
        self.current_timeout = np.clip(1e6 + np.random.randint(-1e5, 1e5), 1e4, 1e9)
        self.current_retries = np.clip(3 + np.random.randint(-1, 2), 1, 10)
        return self._normalize_state()

    def step(self, action):
        # Convert normalized actions to parameter changes
        delta_distance = action[0] * 20  # Max ±20 m change
        delta_timeout = action[1] * 5e4   # Max ±5e4 ns change
        delta_retries = action[2] * 1     # Max ±1 retries change

        # Update parameters with clamping
        self.current_distance = np.clip(
            self.current_distance + delta_distance, 1, 200
        )
        self.current_timeout = np.clip(
            self.current_timeout + delta_timeout, 1, 1e9
        )
        self.current_retries = np.clip(
            self.current_retries + delta_retries, 1, 10
        )

        # Round to valid values
        self.current_distance = int(round(self.current_distance))
        self.current_timeout = int(round(self.current_timeout / 100) * 100)
        self.current_retries = int(round(self.current_retries))

        print(f"distance: {self.current_distance}, timeout: {self.current_timeout}, retiries: {self.current_retries}")
        # Get simulation results
        success_count = avg_100_runs(
            NO_OF_BITS,
            self.current_distance,
            self.current_timeout,
            self.current_retries
        )

        # Calculate composite reward
        distance_reward = self.current_distance / 200
        success_reward = success_count / 100
        reward = distance_reward * success_reward * 100  # Scale reward for better learning

        # Episode continues until terminated manually
        done = False

        return self._normalize_state(), reward, done, {}

# Create and wrap environment
env = DummyVecEnv([lambda: BB84Env()])

# Configure PPO model
model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=0.0003,
    n_steps=1024,
    batch_size=64,
    tensorboard_log="./bb84_ppo_logs/"
)

# Train the model
try:
    model.learn(total_timesteps=100, progress_bar=True)
except KeyboardInterrupt:
    print("Training interrupted")

# Save the trained model
#model.save("bb84_ppo_model")

# Example of using the trained model
trained_model = PPO.load("bb84_ppo_model")
obs = env.reset()

for _ in range(10):
    action, _ = trained_model.predict(obs)
    obs, rewards, _, _ = env.step(action)
    state = env.envs[0]
    print(f"Distance: {state.current_distance} m, "
          f"Timeout: {state.current_timeout} ns, "
          f"Retries: {state.current_retries}, "
          f"Reward: {rewards[0]:.2f}")