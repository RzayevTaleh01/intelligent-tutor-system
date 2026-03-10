import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from typing import Optional, Tuple, Dict, Any

class SimulatedStudent:
    """
    Simulates a student for RL training.
    Uses a simplified BKT-like logic.
    """
    def __init__(self, initial_mastery: float = 0.3, learning_rate: float = 0.1):
        self.mastery = initial_mastery
        self.learning_rate = learning_rate
        self.fatigue = 0.0

    def attempt(self, difficulty: int) -> Tuple[bool, float]:
        """
        Simulates an attempt at a given difficulty (1-5).
        Returns: (is_correct, time_taken)
        """
        # Probability of success depends on mastery vs difficulty
        # Diff 1 (Easy) -> needs low mastery
        # Diff 5 (Hard) -> needs high mastery
        difficulty_factor = difficulty / 5.0
        success_prob = 1.0 / (1.0 + np.exp(10 * (difficulty_factor - self.mastery)))
        
        # Fatigue reduces success chance slightly
        success_prob *= (1.0 - self.fatigue * 0.5)
        
        is_correct = random.random() < success_prob
        
        # Update mastery (Learning)
        if is_correct:
            # Learn more from harder tasks if successful
            gain = self.learning_rate * (1.0 - self.mastery) * (difficulty / 3.0)
        else:
            # Learn a little from mistakes
            gain = self.learning_rate * 0.1
            
        self.mastery = min(1.0, self.mastery + gain)
        self.fatigue = min(1.0, self.fatigue + 0.05) # Gets tired
        
        # Time taken simulation (harder + lower mastery = slower)
        base_time = 10.0 # seconds
        time_taken = base_time * (1.0 + (difficulty_factor - self.mastery)) * random.uniform(0.8, 1.2)
        
        return is_correct, max(1.0, time_taken)

class EduVisionEnv(gym.Env):
    """
    Custom Environment that follows gymnasium interface.
    Represents the interaction between the Pedagogy Engine (Agent) and a Student.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self):
        super(EduVisionEnv, self).__init__()
        
        # Actions: 0=Easier, 1=Same, 2=Harder
        self.action_space = spaces.Discrete(3)
        
        # Observations:
        # 0: Mastery Score (0-1)
        # 1: Last Correct (0 or 1)
        # 2: Current Difficulty (normalized 0-1)
        # 3: Consecutive Errors (normalized 0-1)
        # 4: Fatigue (0-1)
        self.observation_space = spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32)
        
        self.student = None
        self.current_difficulty = 3 # Start at medium
        self.consecutive_errors = 0
        self.last_correct = 1
        self.steps_taken = 0
        self.max_steps = 50

    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None):
        super().reset(seed=seed)
        
        # Initialize a new random student
        initial_mastery = random.uniform(0.1, 0.5)
        lr = random.uniform(0.05, 0.2)
        self.student = SimulatedStudent(initial_mastery, lr)
        
        self.current_difficulty = 3
        self.consecutive_errors = 0
        self.last_correct = 1
        self.steps_taken = 0
        
        return self._get_obs(), {}

    def step(self, action):
        # 1. Apply Action (Adjust Difficulty)
        # Action 0: Decrease
        # Action 1: Maintain
        # Action 2: Increase
        
        prev_difficulty = self.current_difficulty
        
        if action == 0:
            self.current_difficulty = max(1, self.current_difficulty - 1)
        elif action == 2:
            self.current_difficulty = min(5, self.current_difficulty + 1)
            
        # 2. Simulate Student Attempt
        is_correct, time_taken = self.student.attempt(self.current_difficulty)
        
        # 3. Update State
        self.last_correct = 1 if is_correct else 0
        if is_correct:
            self.consecutive_errors = 0
        else:
            self.consecutive_errors += 1
            
        self.steps_taken += 1
        
        # 4. Calculate Reward
        # Goal: Maximize Mastery while keeping engagement (not too easy, not too hard)
        
        reward = 0.0
        
        # Reward for mastery gain (we cheat and look at internal state for training)
        reward += (self.student.mastery * 10.0)
        
        # Penalty for too many errors (frustration)
        if self.consecutive_errors > 2:
            reward -= 5.0
            
        # Penalty for being too easy (boredom) - if correct on easy task
        if is_correct and self.current_difficulty < 3 and self.student.mastery > 0.6:
            reward -= 2.0
            
        # Reward for "Flow" (Correct answer on challenging task)
        if is_correct and self.current_difficulty >= 3:
            reward += 5.0

        # 5. Check Termination
        terminated = False
        truncated = False
        
        if self.steps_taken >= self.max_steps:
            truncated = True
        
        if self.student.mastery > 0.95:
            terminated = True
            reward += 50.0 # Bonus for completion
            
        return self._get_obs(), reward, terminated, truncated, {}

    def _get_obs(self):
        return np.array([
            self.student.mastery,
            float(self.last_correct),
            self.current_difficulty / 5.0,
            min(1.0, self.consecutive_errors / 5.0),
            self.student.fatigue
        ], dtype=np.float32)

    def render(self, mode='human'):
        print(f"Step: {self.steps_taken}, Diff: {self.current_difficulty}, "
              f"Correct: {self.last_correct}, Mastery: {self.student.mastery:.2f}")
