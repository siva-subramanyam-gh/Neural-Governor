import subprocess
import time
import sys
import numpy as np
import joblib  # <--- CHANGED: Using joblib as requested
import warnings

# Suppress sklearn warnings if version mismatch occurs
warnings.filterwarnings("ignore")

# ==========================================
# PART 1: THE NEURAL BRAIN (Predictive AI)
# ==========================================
class NeuralBrain:
    def __init__(self, model_path="thermal_model.pkl"):
        self.model = None
        self.active = False
        
        try:
            # CHANGED: Using joblib to load the model
            with open(model_path, "rb") as f:
                self.model = joblib.load(f)
            self.active = True
            print(f" [AI] Brain Loaded: {model_path}")
        except FileNotFoundError:
            print(f" [AI] CRITICAL: {model_path} not found! Running in dumb reactive mode.")
        except Exception as e:
            print(f" [AI] Error loading model: {e}")

    def predict_future(self, current_temp):
        """
        Input: Current Battery Temp (e.g., 38.5)
        Output: Predicted Temp in 5 mins (e.g., 43.2)
        """
        if not self.active:
            return current_temp # Fallback: Assume future = current (Reactive)

        try:
            # Reshape for sklearn: [[38.5]]
            input_val = np.array([[current_temp]])
            prediction = self.model.predict(input_val)
            return float(prediction[0])
        except Exception as e:
            # If prediction fails (e.g. shape mismatch), stay safe and return current temp
            return current_temp

# ==========================================
# PART 2: THE UNIVERSAL MECHANIC (Hardware)
# ==========================================
class UniversalHardware:
    def __init__(self):
        self.clusters = {} 
        self.gears = {}    
        
        print(" [INIT] Starting Universal Neural Governor...")
        self.check_adb()
        self.kill_thermal_services()
        self.detect_hardware()
        self.calculate_gears()
        
    def check_adb(self):
        """Verifying ADB connection and Root access."""
        try:
            # Check connection
            subprocess.check_output("adb devices", shell=True)
            # Check Root
            root_check = self.adb_command("id")
            if "uid=0(root)" not in root_check:
                print(" [ERROR] Root access missing! Please grant Root to Shell/ADB.")
                print("         Run 'adb shell su' manually to trigger the popup.")
                sys.exit(1)
            print(" [OK] ADB Connected & Rooted.")
        except Exception as e:
            print(f" [FATAL] ADB Error: {e}")
            sys.exit(1)

    def adb_command(self, cmd):
        """Executes a shell command with Root privileges."""
        full_cmd = f'adb shell "su -c \'{cmd}\'"'
        try:
            result = subprocess.check_output(full_cmd, shell=True, stderr=subprocess.STDOUT)
            return result.decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            return ""

    def kill_thermal_services(self):
        """The 'Hit List': Auto-kills known thermal managers."""
        print(" [OP] Neutralizing System Thermal Managers...")
        hit_list = [
            "mi_thermald", "vendor.thermal-engine", "thermal-engine", 
            "android.hardware.thermal@2.0-service", "android.hardware.thermal@2.0-service.qti",
            "thermald", "triton"
        ]
        
        for daemon in hit_list:
            self.adb_command(f"stop {daemon}")
            self.adb_command(f"killall {daemon}")
            
        print(" [OK] Thermal services suppressed.")

    def detect_hardware(self):
        """Scans /sys/devices to find CPU clusters and their limits."""
        print(" [SCAN] Detecting CPU Topology...")
        raw_policies = self.adb_command("ls -d /sys/devices/system/cpu/cpufreq/policy*")
        
        if not raw_policies:
            print(" [ERROR] No CPU policies found! Is the kernel standard?")
            sys.exit(1)
            
        policy_paths = raw_policies.splitlines()
        
        for path in policy_paths:
            policy_name = path.split("/")[-1]
            freqs_str = self.adb_command(f"cat {path}/scaling_available_frequencies")
            if not freqs_str:
                continue              
            freqs = sorted([int(f) for f in freqs_str.split() if f.isdigit()])
            
            self.clusters[policy_name] = {
                "path": path,
                "freqs": freqs
            }
            print(f"    Found {policy_name}: {len(freqs)} steps ({freqs[0]//1000}MHz - {freqs[-1]//1000}MHz)")

    def calculate_gears(self):
        """Dynamically calculates 4 Gear levels based on the specific hardware found."""
        print(" [CALC] Calculating Gear Ratios...")
        for policy, data in self.clusters.items():
            freqs = data['freqs']
            count = len(freqs)         
            self.gears[policy] = {
                1: freqs[0],                # Gear 1: Min (Cool Down)
                2: freqs[int(count * 0.33)],# Gear 2: Braking
                3: freqs[int(count * 0.66)],# Gear 3: Sustainable
                4: freqs[-1]                # Gear 4: Turbo
            }
        print(" [OK] Gears Calibrated.")

    def apply_gear(self, gear_level):
        """Applies the gear to ALL clusters using schedutil + hard clamping."""
        for policy, data in self.clusters.items():
            base_path = data['path']
            target_freq = self.gears[policy][gear_level]
            
            commands = [
                f"echo schedutil > {base_path}/scaling_governor",
                f"echo {data['freqs'][0]} > {base_path}/scaling_min_freq", # Reset floor first
                f"echo {target_freq} > {base_path}/scaling_max_freq",      # Set Ceiling
                f"echo {target_freq} > {base_path}/scaling_min_freq"       # Raise Floor to match Ceiling
            ]
            full_cmd = " && ".join(commands)
            self.adb_command(full_cmd)

    def get_battery_temp(self):
        """Reads battery temp. Universal fallback logic."""
        res = self.adb_command("dumpsys battery | grep temperature")
        if res:
            try:
                temp_raw = int(res.split(":")[1].strip())
                return temp_raw / 10.0
            except: pass
        
        # Fallback to sysfs
        zones = ["thermal_zone0", "thermal_zone1", "thermal_zone2"]
        for zone in zones:
            res = self.adb_command(f"cat /sys/class/thermal/{zone}/type")
            if "battery" in res.lower():
                try:
                    temp_str = self.adb_command(f"cat /sys/class/thermal/{zone}/temp")
                    return int(temp_str) / 1000.0
                except: continue
        return 0.0

# ==========================================
# PART 3: THE CONTROLLER (Main Loop)
# ==========================================
class NeuralGovernor:
    def __init__(self):
        print("\n=== NEURAL GOVERNOR INITIATING ===")
        self.brain = NeuralBrain()      # The AI
        self.mech = UniversalHardware() # The Hardware
        
        # Stability Settings
        self.current_gear = 4
        self.last_shift_time = 0
        self.shift_cooldown = 3.0 # Seconds between shifts

    def run(self):
        print(" [START] Active. Monitoring Battery Temps...")
        
        while True:
            # 1. Sense (Real World)
            real_temp = self.mech.get_battery_temp()
            
            # 2. Think (Predictive AI)
            pred_temp = self.brain.predict_future(real_temp)
            
            # 3. Decide (Based on Prediction)
            target_gear = 4 # Default to Turbo
            if pred_temp > 42.0:
                target_gear = 1  # Emergency
            elif pred_temp > 39.0:
                target_gear = 2  # Braking
            elif pred_temp > 37.0:
                target_gear = 3  # Sustainable
            else:
                target_gear = 4  # Turbo

            # 4. Act (Stability Logic)
            self.execute_shift(real_temp, pred_temp, target_gear)
            
            time.sleep(1.0)

    def execute_shift(self, real, pred, target):
        now = time.time()
        time_since_shift = now - self.last_shift_time
        
        # Update Status Line (Overwrites previous line)
        status = f"\r [REAL: {real}°C] -> [AI PRED: {pred:.1f}°C] | Gear: {self.current_gear}"
        sys.stdout.write(status + " " * 10) 
        sys.stdout.flush()

        # RULE 1: Only act if the gear needs to change
        if target != self.current_gear:
            
            # RULE 2: PANIC OVERRIDE (Safety First)
            is_emergency = (target == 1)
            
            # RULE 3: COOLDOWN CHECK
            if time_since_shift > self.shift_cooldown or is_emergency:
                print(f"\n [SHIFT] AI Predicted {pred:.1f}°C. Shifting Gear {self.current_gear} -> {target}")
                self.mech.apply_gear(target)
                self.current_gear = target
                self.last_shift_time = now

if __name__ == "__main__":
    app = NeuralGovernor()
    app.run()