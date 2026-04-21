import subprocess
import time
import sys

def run_script(script_path):
    """"Function untuk running script python and check error"""
    print(f"\n [Running]{script_path}..")
    result = subprocess.run([sys.executable,script_path],capture_output=True, text =True)
    
    if result.returncode == 0:
        print(f"Success {script_path}")
        print(result.stdout)
        return True
    else:
        print(f"[Failed] {script_path}")
        print(result.stderr)
        return False
    
def main():
    start_time = time.time()
    print("Start weather data pipeline")
    
    if run_script("scripts/ingest_weather.py"):
        #jalanin script ingest
        run_script("scripts/transform_weather.py")
    
    end_time = time.time()
    duration = round(end_time - start_time,2)
    print(f"pipeline finished in {duration} seconds")
    
if __name__ == "__main__":
    main()