import pandas as pd
import numpy as np

def process_data():
    input_file="phone_stats.csv"
    output_file="train_processed_data.csv"    #Declaring both input files and processed file(CSV) for syntax convenience
    try:
        df=pd.read_csv(input_file)
        print(f"Opened file and got {len(df)} records.")
    except FileNotFoundError:
        print(f"Input File: {input_file} not found.") # Checking whether the file is actua
        return
    df['TimeStamp']=pd.to_datetime(df['TimeStamp'],format='%H:%M:%S') # Formating the default collected date time to a hh:mm:ss format
    df = df.sort_values(by='TimeStamp')
    df['Time_Diff'] = df['TimeStamp'].diff().dt.total_seconds()
    df['Session_ID'] = (df['Time_Diff'] > 30).cumsum()
    start_time=df['TimeStamp'].iloc[0] #We collect the first value of the time stamp in the input data
    df['Seconds_Run']=(df['TimeStamp']-start_time).dt.total_seconds()  
    df['Temp_Smooth'] = df.groupby('Session_ID')['Battery_temp'].transform(lambda x: x.rolling(window=3, min_periods=1).mean()) #Calculating a rolling mean for the temparatures to prevent 0's due to precision 
    df['Temp_Velocity'] = df.groupby('Session_ID')['Temp_Smooth'].diff()
    if 'GPU_Load' not in df.columns:
        df['GPU_Load'] = 0.0        #We are preventing the possibility of empty string in data when load becomes null 
    df['Stress_Score'] = (df['CPU_Freq'] / 3000) + (df['GPU_Load'] / 100)
    df['Stress_Score'] = df.groupby('Session_ID')['Stress_Score'].shift(1)
    df = df.dropna(subset=['Temp_Velocity', 'Stress_Score'])
    df.to_csv("training_data_processed.csv", index=False)
    print("-" * 40)
    print(f"Success! Processed data saved to: {output_file}")
    print(f"Samples remaining after cleaning: {len(df)}")
    print("-" * 40)
    print("Data Preview (Head):")
    print(df[['Seconds_Run', 'Battery_temp', 'Temp_Smooth', 'Temp_Velocity', 'Stress_Score']].head())
    print("-" * 40)
    #Check for if the phone actually did some work while the data was collected
    max_heat_rate = df['Temp_Velocity'].max()
    print(f"Max Heating Rate observed: {max_heat_rate:.4f} °C/step")
    if max_heat_rate==0:
        print("WARNING: Max heating rate is 0(phone was idle).")
        print("Try running a game or using it to get better training data.")
if __name__=="__main__":
    process_data()
