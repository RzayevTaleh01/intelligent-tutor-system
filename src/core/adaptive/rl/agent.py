import os
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from src.core.adaptive.rl.env import EduVisionEnv

import torch

MODEL_PATH = "models/rl/ppo_pedagogy_v1"

class RLAgent:
    def __init__(self, training_mode=False):
        self.model = None
        self.env = None
        
        # Determine device
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"🔥 RL Agent using device: {self.device}")
        
        if training_mode:
            self.env = make_vec_env(lambda: EduVisionEnv(), n_envs=4)
        
        # Load existing model if available
        if os.path.exists(f"{MODEL_PATH}.zip"):
            try:
                self.model = PPO.load(MODEL_PATH, device=self.device)
                print(f"Loaded RL model from {MODEL_PATH}")
            except Exception as e:
                print(f"Failed to load model: {e}")
        
        if self.model is None and training_mode:
            print("Initializing new PPO model...")
            self.model = PPO("MlpPolicy", self.env, verbose=1, device=self.device)

    def train(self, total_timesteps=10000):
        if self.model is None:
            raise ValueError("Model not initialized. Set training_mode=True.")
            
        print(f"Training RL Agent for {total_timesteps} steps...")
        self.model.learn(total_timesteps=total_timesteps)
        
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        self.model.save(MODEL_PATH)
        print(f"Model saved to {MODEL_PATH}")

    def predict(self, observation):
        """
        Predicts the next action based on observation.
        Observation: [mastery, last_correct, difficulty_norm, errors_norm, fatigue]
        """
        if self.model is None:
            # Fallback if model missing (e.g. random or heuristic)
            return 1 # Default: Maintain difficulty
            
        action, _states = self.model.predict(observation, deterministic=True)
        return int(action)

if __name__ == "__main__":
    # Test Training
    agent = RLAgent(training_mode=True)
    agent.train(total_timesteps=5000)
