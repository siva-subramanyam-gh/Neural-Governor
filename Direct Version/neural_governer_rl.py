import subprocess
import time
import sys
import numpy as np
import os
import pickle
import random

# ==========================================
# PART 1: THE BRAIN (Reinforcement Learning)
# "The Dog that learns from treats and scoldings"
# ==========================================
class RLBrain:
    def __init__(self, model_path="q_table.pkl"):
        # The Q-Table is just a "Cheat Sheet".
        # It maps States (Temperature) -> Actions (Gears) -> Value (How good was it?)
        self.q_table = {} 
        self.model_path = model_path
        
        # Hyperparameters (The personality of my AI)
        self.learning_rate = 0.1  # How fast it accepts new info (10% new, 90% memory)
        self.discount_factor = 0.9 # How much it cares about future heat vs immediate speed
        self.epsilon = 0.1        # Curiosity: 10% of the time, try a random gear just to see what happens
        
        self.last_state = None
        self.last_action = None
        
        # Try to load existing brain (memory)
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    self.q_table = pickle.load(f)
                print(f" [RL] Brain Loaded. I remember {len(self.q_table)} thermal scenarios.")
            except: 
                print(" [RL] Brain corrupted. Starting fresh.")

    def save_brain(self):
        # Save the cheat sheet so we don't forget what we learned
        with open(self.model_path, "wb") as f:
            pickle.dump(self.q_table, f)

    def get_state(self, temp):
        # Simplify the world. The AI doesn't need to know 38.123°C.
        # It just needs to know "It's roughly 38.0°C".
        # Rounding to nearest 0.5 creates "Buckets" for our state.
        return int(round(temp * 2)) / 2

    def choose_action(self, current_temp):
        state = self.get_state(current_temp)
        
        # If I've never seen this temperature before, initialize it
        if state not in self.q_table:
            # [Gear 1, Gear 2, Gear 3, Gear 4] - Start with zeros (neutral)
            self.q_table[state] = [0.0, 0.0, 0.0, 0.0]

        # The "Coin Flip" (Exploration vs Exploitation)
        if random.uniform(0, 1) < self.epsilon:
            # Explore: Try something random! Maybe Gear 1 works better than I thought?
            action_index = random.randint(0, 3) 
        else:
            # Exploit: Do what I KNOW works best (Highest value in table)
            action_index = np.argmax(self.q_table[state])

        # Return Gear (1-4)
        return action_index + 1

    def learn(self, current_temp):
        """
        The Core Logic: Did my last action result in a Treat or a Scolding?
        """
        # Can't learn if I haven't done anything yet
        if self.last_state is None or self.last_action is None:
            return

        current_state = self.get_state(current_temp)
        
        # Ensure state exists in memory
        if current_state not in self.q_table:
            self.q_table[current_state] = [0.0, 0.0, 0.0, 0.0]

        # === THE TEACHER (Reward Function) ===
        reward = 0
        
        # SCENARIO 1: Overheating (The "Bad Dog" Scolding)
        # If I let the phone melt, HUGE penalty.
        if current_temp > 43.0:
            reward = -20 
        elif current_temp > 41.0:
            reward = -10

        # SCENARIO 2: Performance (The "Good Boy" Treat)
        # If the phone is cool (<40) AND I used High Gear (Gear 4), give a treat!
        # We want speed, but only when safe.
        elif current_temp < 40.0:
            if self.last_action == 3: # Gear 4 (Index 3)
                reward = +10 # Perfect! Fast and Cool.
            elif self.last_action == 0: # Gear 1 (Index 0)
                reward = -5  # Why are you slow? It's cool enough to run fast!

        # === THE MATH (Bellman Equation) ===
        # New_Value = Old_Value + Learning_Rate * (Reward + Discount * Best_Future_Value - Old_Value)
        
        old_value = self.q_table[self.last_state][self.last_action]
        next_max = np.max(self.q_table[current_state])
        
        new_value = old_value + self.learning_rate * (reward + self.discount_factor * next_max - old_value)
        
        # Update Memory
        self.q_table[self.last_state][self.last_action] = new_value
        self.save_brain()

# ==========================================
# PART 2: THE MECHANIC (Termux Edition)
# ==========================================
class UniversalHardware:
    def __init__(self):
        self.clusters = {} 
        self.gears = {}    
        print(" [INIT] Connecting to Local Kernel...")
        self.check_root()
        self.detect_cpu()
        self.calculate_gears()
        
    def check_root(self):
        # In Termux, we just check if we can run 'id' as root
        try:
            if "uid=0(root)" not in self.run_shell("id"):
                print(" [ERROR] Termux needs Root! Run 'tsu' before starting Python.")
                sys.exit(1)
        except: 
            print(" [ERROR] Root check failed.")
            sys.exit(1)

    def run_shell(self, cmd):
        # DIRECT ROOT EXECUTION (No ADB)
        # We use 'su -c' to run the command as the Superuser
        full_cmd = f'su -c "{cmd}"'
        try:
            return subprocess.check_output(full_cmd, shell=True).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            return ""

    def detect_cpu(self):
        # Same logic, just different transport
        raw = self.run_shell("ls -d /sys/devices/system/cpu/cpufreq/policy*")
        if not raw:
            print(" [ERROR] Could not find CPU policies.")
            sys.exit(1)
            
        for path in raw.splitlines():
            freqs_str = self.run_shell(f"cat {path}/scaling_available_frequencies")
            if freqs_str:
                freqs = sorted([int(f) for f in freqs_str.split() if f.isdigit()])
                self.clusters[path.split("/")[-1]] = {"path": path, "freqs": freqs}

    def calculate_gears(self):
        for policy, data in self.clusters.items():
            f = data['freqs']
            self.gears[policy] = {
                1: f[0], 2: f[int(len(f)*0.4)], 3: f[int(len(f)*0.7)], 4: f[-1]
            }
        print(f" [OK] Detected {len(self.clusters)} CPU Clusters.")

    def apply_gear(self, gear):
        for policy, data in self.clusters.items():
            path = data['path']
            target = self.gears[policy][gear]
            min_freq = data['freqs'][0]
            
            # 1. Unlock
            cmds = [f"chmod 644 {path}/scaling_max_freq", f"chmod 644 {path}/scaling_min_freq"]
            
            # 2. Set Values
            cmds.append(f"echo {min_freq} > {path}/scaling_min_freq")
            cmds.append(f"echo {target} > {path}/scaling_max_freq")
            
            # 3. Lock Ceiling
            cmds.append(f"chmod 444 {path}/scaling_max_freq")
            
            # Execute batch
            self.run_shell(" && ".join(cmds))

    def get_temp(self):
        try: return int(self.run_shell("cat /sys/class/power_supply/battery/temp")) / 10.0
        except: return 0.0

# ==========================================
# PART 3: THE GOVERNOR (Main Loop)
# ==========================================
class NeuralGovernor:
    def __init__(self):
        print("\n=== NEURAL GOVERNOR: RL EDITION (TERMUX) ===")
        self.brain = RLBrain()          # The AI
        self.mech = UniversalHardware() # The Termux/Root Interface
        self.current_gear = 0           # Start with no gear applied

    def run(self):
        print(" [START] Monitoring...")
        while True:
            try:
                # 1. SENSE (Get Temp)
                real_temp = self.mech.get_temp()
                
                # 2. LEARN (Did the last action work?)
                # The brain looks at the current temp + previous state to calculate reward
                self.brain.learn(real_temp)
                
                # 3. DECIDE (Pick best gear for this temp)
                # The brain consults its Q-Table or explores (epsilon-greedy)
                target_gear = self.brain.choose_action(real_temp)
                
                # 4. MEMORIZE (Store state for next learning cycle)
                # We must update the "last state" so the brain knows "Previous Context"
                self.brain.last_state = self.brain.get_state(real_temp)
                self.brain.last_action = target_gear - 1 # Store index 0-3
                
                # 5. ACT (Apply Gear to Hardware)
                if target_gear != self.current_gear:
                    print(f"\n [SHIFT] Temp: {real_temp:.1f}°C. Adaptive Logic chose Gear {target_gear}")
                    self.mech.apply_gear(target_gear)
                    self.current_gear = target_gear
                else:
                    # Erasable status line to keep terminal clean
                    sys.stdout.write(f"\r [MONITOR] Temp: {real_temp:.1f}°C | Gear: {self.current_gear}   ")
                    sys.stdout.flush()
                    
                time.sleep(1.0) # Run loop every second

            except KeyboardInterrupt:
                print("\n [STOP] Saving Brain and Exiting...")
                self.brain.save_brain()
                sys.exit(0)
            except Exception as e:
                print(f"\n [ERROR] Loop crash: {e}")
                time.sleep(2) # Wait before retrying

if __name__ == "__main__":
    NeuralGovernor().run()