from datetime import datetime, timedelta
import os
import json
import matplotlib.pyplot as plt
import pathlib as p

DEBUG: bool = True

# Assuming the log file format is JSON with keys "total" and "free" for each day
GLOBAL_FSMON_CONFIG = {
    "plot_path": "./graphs/usage_chart.png",
    "log_files_path": "./dblog",
    "days_to_parse": 7,
}

def init_directories(plot_path: str="./dblog"):
    try:
        if not os.path.exists(os.path.dirname(plot_path)):
            os.makedirs(os.path.dirname(plot_path))
    except:
        if DEBUG:
            print(f"Error creating directories for {plot_path}")

def load_db_data(log_file_path) -> dict:
    try:
        with open(log_file_path, 'r') as file:
            log_data = json.load(file)
        return log_data
    except FileNotFoundError:
        if DEBUG:
            print(f"The file {log_file_path} does not exist.")
        return {}

def get_usage_data(log_files_path: str, days: int=7) -> list:
    usage_data = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        log_file_name = date.strftime('%Y-%m-%d') + '.log'
        log_file_path = os.path.join(log_files_path, log_file_name)
        try:
            log_data = load_db_data(log_file_path)
        except:
            pass
        if log_data:
            total_space = round(log_data["total"], 2)
            used_space = round(total_space - log_data["free"], 2)
            usage_data.append((date, used_space))
    return usage_data

def create_weekly_graph(usage_data: list, plot_path: str):
    if not usage_data:
        if DEBUG:
            print("No usage data available to plot.")
        return

    dates = [data[0] for data in usage_data]
    usages = [data[1] for data in usage_data]
    
    plt.figure(figsize=(10, 5))
    plt.plot(dates, usages, marker='o')
    plt.xlabel('Date')
    plt.ylabel('Usage (GB)')
    plt.title('File System Usage for the Week')
    plt.grid(True)
    plt.gcf().autofmt_xdate()  # Rotate dates for better readability
    plt.savefig(plot_path)
    plt.close()
    if DEBUG:
        print(f"Graph saved to {plot_path}")

if __name__ == "__main__":
    init_directories(GLOBAL_FSMON_CONFIG['plot_path'])
    usage_data = get_usage_data(GLOBAL_FSMON_CONFIG['log_files_path'], GLOBAL_FSMON_CONFIG['days_to_parse'])
    create_weekly_graph(usage_data, GLOBAL_FSMON_CONFIG['plot_path'])
