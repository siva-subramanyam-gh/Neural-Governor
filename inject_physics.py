import pandas as pd
import numpy as np

def inject_physics():
    print("---Data Injection ---")

    try:
        df = pd.read_csv("training_data_processed.csv")
        print(f"Loaded {len(df)} rows of real data.")
    except FileNotFoundError:
        print("Error: Run preprocess.py first!")
        return

    # 2. Create Synthetic "Cooling" Data
    # We simulate a phone cooling from 50°C to 30°C with ZERO stress.
    synthetic_rows = []
    
    for temp in range(30, 50):
        # Physics Rule: The hotter it is, the faster it cools.
        # Newton's Law of Cooling: Velocity = -k * (Temp - Ambient)
        # We assume Ambient = 28°C, k = 0.05
        ambient_temp = 28.0
        cooling_velocity = -0.05 * (temp - ambient_temp)
        
        # Add some noise so it looks real to the AI
        for _ in range(20): # Make 20 copies of each degree to weight the training
            row = {
                'Stress_Score': 0.0,       # Doing nothing
                'Temp_Smooth': float(temp),
                'Temp_Velocity': cooling_velocity + np.random.normal(0, 0.01)
            }
            synthetic_rows.append(row)
            
    # 3. Create Synthetic "Heating" Data (To balance it)
    # Stress = 1.0 (Max), Temp = 30°C (Start of gaming)
    # It should heat up FAST.
    for _ in range(100):
        row = {
            'Stress_Score': 1.0,
            'Temp_Smooth': 30.0,
            'Temp_Velocity': 0.5 + np.random.normal(0, 0.02) # Heats up by 0.5°C per step
        }
        synthetic_rows.append(row)

    # 4. Merge and Save
    synthetic_df = pd.DataFrame(synthetic_rows)
    final_df = pd.concat([df, synthetic_df], ignore_index=True)
    
    # Shuffle the data so the AI doesn't memorize the order
    final_df = final_df.sample(frac=1).reset_index(drop=True)
    
    final_df.to_csv("train_augmented_data.csv", index=False)
    print(f"Injected {len(synthetic_df)} physics rows.")
    print(f"Saved {len(final_df)} rows to 'train_augmented_data.csv'.")

if __name__ == "__main__":
    inject_physics()