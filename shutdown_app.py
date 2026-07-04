import os
import sys
import json
import time
import argparse
import subprocess
import threading
from datetime import datetime, timedelta

# Import customtkinter for GUI
# 导入 customtkinter 用于 GUI 界面
try:
    import customtkinter as ctk
except ImportError:
    print("Error: customtkinter is not installed. Please run: pip install customtkinter")
    sys.exit(1)

# File path to save shutdown state
# 保存关机状态的文件路径
STATUS_FILE = os.path.join(os.path.expanduser("~"), ".win_shutdown_status.json")

def save_status(target_time, mode, val_str):
    """
    Save shutdown task status to a local file.
    保存关机任务状态到本地文件。
    """
    data = {
        "target_timestamp": target_time.timestamp(),
        "mode": mode,  # "delay" or "time"
        "value": val_str,
        "created_at": datetime.now().timestamp()
    }
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Failed to save status file / 无法保存状态文件: {e}")

def clear_status():
    """
    Clear the saved shutdown task status.
    清除已保存的关机任务状态。
    """
    if os.path.exists(STATUS_FILE):
        try:
            os.remove(STATUS_FILE)
        except Exception as e:
            print(f"Failed to remove status file / 无法删除状态文件: {e}")

def get_saved_status():
    """
    Read the saved shutdown task status. Returns None if invalid or expired.
    读取已保存的关机任务状态。若无效或已过期，则返回 None。
    """
    if not os.path.exists(STATUS_FILE):
        return None
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        target_timestamp = data.get("target_timestamp", 0)
        target_time = datetime.fromtimestamp(target_timestamp)
        # If the target time is in the future, it's valid
        # 如果目标时间在未来，则状态有效
        if target_time > datetime.now():
            return data
        else:
            clear_status()
    except Exception:
        clear_status()
    return None

def execute_shutdown(seconds):
    """
    Execute Windows shutdown command.
    执行 Windows shutdown 关机命令。
    """
    # shutdown -s -t <seconds>
    # /s = shutdown, /t = delay in seconds
    try:
        subprocess.run(["shutdown", "-s", "-t", str(seconds)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing shutdown command / 执行关机命令错误: {e}")
        return False

def cancel_shutdown():
    """
    Cancel Windows shutdown command.
    取消 Windows shutdown 关机命令。
    """
    # shutdown -a
    # /a = abort shutdown
    try:
        subprocess.run(["shutdown", "-a"], check=True)
        clear_status()
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error canceling shutdown command / 取消关机命令错误 (可能当前没有处于计划中的关机): {e}")
        clear_status()
        return False

def set_shutdown_by_delay(hours, minutes):
    """
    Set shutdown by relative delay.
    设置相对延迟关机。
    """
    total_seconds = int(hours * 3600 + minutes * 60)
    if total_seconds <= 0:
        return False, "Delay must be greater than 0 / 延迟时间必须大于0"
    
    # Cancel any existing shutdown first
    # 首先取消任何已存在的关机任务
    cancel_shutdown()
    
    success = execute_shutdown(total_seconds)
    if success:
        target_time = datetime.now() + timedelta(seconds=total_seconds)
        save_status(target_time, "delay", f"{hours}h {minutes}m")
        return True, f"Shutdown scheduled in {hours}h {minutes}m (at {target_time.strftime('%Y-%m-%d %H:%M:%S')}) / 已设定在 {hours}小时 {minutes}分钟 后关机"
    return False, "Failed to schedule shutdown / 设定关机失败"

def set_shutdown_by_time(time_str):
    """
    Set shutdown at an exact time (format HH:MM).
    设置在绝对时间点关机 (格式 HH:MM)。
    """
    try:
        target_hm = datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return False, "Invalid time format. Use HH:MM (e.g. 23:30) / 时间格式无效，请使用 HH:MM 格式"
        
    now = datetime.now()
    target_time = now.replace(hour=target_hm.hour, minute=target_hm.minute, second=0, microsecond=0)
    
    # If the time has already passed today, set it for tomorrow
    # 如果该时间在今天已经过去，则设定在明天同一时刻
    if target_time <= now:
        target_time += timedelta(days=1)
        
    total_seconds = int((target_time - now).total_seconds())
    
    # Cancel any existing shutdown first
    # 首先取消任何已存在的关机任务
    cancel_shutdown()
    
    success = execute_shutdown(total_seconds)
    if success:
        save_status(target_time, "time", time_str)
        return True, f"Shutdown scheduled at {target_time.strftime('%Y-%m-%d %H:%M:%S')} / 已设定在 {target_time.strftime('%Y-%m-%d %H:%M:%S')} 关机"
    return False, "Failed to schedule shutdown / 设定关机失败"

class ShutdownApp(ctk.CTk):
    """
    Windows 11 themed UI for scheduled shutdown.
    Windows 11 风格的定时关机 GUI 界面。
    """
    def __init__(self):
        super().__init__()
        
        # Window configuration
        # 窗口基本配置
        self.title("Windows 11 定时关机助手")
        self.geometry("520x480")
        self.resizable(False, False)
        
        # Set themes (follows system or default dark)
        # 设置主题 (跟从系统或默认暗色)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.active_task = None
        self.running_thread = None
        self.stop_thread_event = threading.Event()
        
        # Render the UI Components
        # 渲染 UI 组件
        self.setup_ui()
        
        # Check if there is an active shutdown task
        # 检查是否已有活跃的关机任务
        self.check_existing_task()

    def setup_ui(self):
        # Title Label
        # 标题标签
        self.title_label = ctk.CTkLabel(
            self, 
            text="Win11 定时关机工具", 
            font=ctk.CTkFont(family="Microsoft YaHei", size=22, weight="bold")
        )
        self.title_label.pack(pady=(20, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self, 
            text="简约、高效的系统计划关机助手", 
            text_color="gray",
            font=ctk.CTkFont(family="Microsoft YaHei", size=13)
        )
        self.subtitle_label.pack(pady=(0, 15))
        
        # Tab View for choosing Delay or Time
        # 选项卡控件，用于选择倒计时或指定时刻
        self.tabview = ctk.CTkTabview(self, width=460, height=200)
        self.tabview.pack(pady=10)
        
        self.tab_delay = self.tabview.add("倒计时模式 (Countdown)")
        self.tab_time = self.tabview.add("指定时间模式 (Specific Time)")
        
        # Setup Countdown Tab
        # 设置倒计时标签页
        self.setup_delay_tab()
        
        # Setup Specific Time Tab
        # 设置特定时间标签页
        self.setup_time_tab()
        
        # Task Status Section
        # 任务状态展示栏
        self.status_frame = ctk.CTkFrame(self, width=460, height=120)
        self.status_frame.pack_propagate(False)
        self.status_frame.pack(pady=(10, 20))
        
        self.status_title = ctk.CTkLabel(
            self.status_frame, 
            text="当前任务状态 / Current Status:", 
            font=ctk.CTkFont(family="Microsoft YaHei", size=12, weight="bold")
        )
        self.status_title.pack(anchor="w", padx=15, pady=(8, 2))
        
        self.status_desc = ctk.CTkLabel(
            self.status_frame, 
            text="未设定关机任务 (No task scheduled)", 
            font=ctk.CTkFont(family="Microsoft YaHei", size=13)
        )
        self.status_desc.pack(padx=15, pady=2)
        
        # Cancel Button
        # 取消按钮
        self.btn_cancel = ctk.CTkButton(
            self.status_frame, 
            text="取消计划关机 (Cancel Shutdown)", 
            fg_color="#D9383A", 
            hover_color="#B32426",
            command=self.on_cancel,
            state="disabled"
        )
        self.btn_cancel.pack(pady=(8, 8))

    def setup_delay_tab(self):
        # Hour Slider Frame
        # 小时滑动条框架
        self.h_frame = ctk.CTkFrame(self.tab_delay, fg_color="transparent")
        self.h_frame.pack(fill="x", padx=20, pady=8)
        
        self.lbl_hour = ctk.CTkLabel(self.h_frame, text="小时 (Hours): 00", width=120, anchor="w", font=ctk.CTkFont(family="Microsoft YaHei", size=12))
        self.lbl_hour.pack(side="left")
        
        self.slider_hour = ctk.CTkSlider(self.h_frame, from_=0, to=24, number_of_steps=24, command=self.update_hour_label)
        self.slider_hour.set(0)
        self.slider_hour.pack(side="right", fill="x", expand=True)
        
        # Minute Slider Frame
        # 分钟滑动条框架
        self.m_frame = ctk.CTkFrame(self.tab_delay, fg_color="transparent")
        self.m_frame.pack(fill="x", padx=20, pady=8)
        
        self.lbl_minute = ctk.CTkLabel(self.m_frame, text="分钟 (Minutes): 30", width=120, anchor="w", font=ctk.CTkFont(family="Microsoft YaHei", size=12))
        self.lbl_minute.pack(side="left")
        
        self.slider_minute = ctk.CTkSlider(self.m_frame, from_=0, to=59, number_of_steps=59, command=self.update_minute_label)
        self.slider_minute.set(30)
        self.slider_minute.pack(side="right", fill="x", expand=True)
        
        # Submit Button
        # 设定按钮
        self.btn_set_delay = ctk.CTkButton(self.tab_delay, text="开始倒计时关机 (Start Countdown)", command=self.on_set_delay)
        self.btn_set_delay.pack(pady=(15, 5))

    def setup_time_tab(self):
        self.time_input_frame = ctk.CTkFrame(self.tab_time, fg_color="transparent")
        self.time_input_frame.pack(pady=20)
        
        self.lbl_time_prompt = ctk.CTkLabel(self.time_input_frame, text="输入关机时间 (HH:MM): ", font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.lbl_time_prompt.pack(side="left", padx=10)
        
        # Pre-fill with current time + 1 hour as hint
        # 用当前时间加一小时作为提示填充
        hint_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
        self.entry_time = ctk.CTkEntry(self.time_input_frame, width=120, placeholder_text=hint_time)
        self.entry_time.insert(0, hint_time)
        self.entry_time.pack(side="left", padx=10)
        
        self.btn_set_time = ctk.CTkButton(self.tab_time, text="设定指定时间关机 (Set Scheduled Time)", command=self.on_set_time)
        self.btn_set_time.pack(pady=(10, 5))

    def update_hour_label(self, val):
        self.lbl_hour.configure(text=f"小时 (Hours): {int(val):02d}")

    def update_minute_label(self, val):
        self.lbl_minute.configure(text=f"分钟 (Minutes): {int(val):02d}")

    def check_existing_task(self):
        data = get_saved_status()
        if data:
            self.active_task = data
            self.start_countdown_thread()
        else:
            self.update_status_ui_idle()

    def update_status_ui_idle(self):
        self.status_desc.configure(text="未设定关机任务 (No task scheduled)", text_color="gray")
        self.btn_cancel.configure(state="disabled")

    def start_countdown_thread(self):
        # Stop existing thread if any
        # 停止任何已存在的计时线程
        self.stop_thread_event.set()
        if self.running_thread and self.running_thread.is_alive():
            self.running_thread.join()
            
        self.stop_thread_event.clear()
        self.btn_cancel.configure(state="normal")
        
        self.running_thread = threading.Thread(target=self.countdown_loop, daemon=True)
        self.running_thread.start()

    def countdown_loop(self):
        while not self.stop_thread_event.is_set():
            if not self.active_task:
                break
                
            target_ts = self.active_task.get("target_timestamp", 0)
            now_ts = datetime.now().timestamp()
            diff = int(target_ts - now_ts)
            
            if diff <= 0:
                self.active_task = None
                self.after(0, self.update_status_ui_idle)
                break
                
            # Calculate readable string
            # 计算可读字符串
            hours, remainder = divmod(diff, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            target_str = datetime.fromtimestamp(target_ts).strftime('%H:%M:%S')
            display_text = f"将在 {hours:02d}:{minutes:02d}:{seconds:02d} 后关机 (预计时刻: {target_str})"
            
            self.after(0, self.update_status_label_text, display_text)
            time.sleep(1)

    def update_status_label_text(self, text):
        self.status_desc.configure(text=text, text_color="#1F6AA5")

    def on_set_delay(self):
        h = int(self.slider_hour.get())
        m = int(self.slider_minute.get())
        if h == 0 and m == 0:
            # Cannot set 0 duration
            # 无法设定0时长的关机
            self.status_desc.configure(text="错误: 时间不能为零 (Time cannot be zero)", text_color="#D9383A")
            return
            
        success, msg = set_shutdown_by_delay(h, m)
        if success:
            self.check_existing_task()
        else:
            self.status_desc.configure(text=msg, text_color="#D9383A")

    def on_set_time(self):
        time_str = self.entry_time.get().strip()
        success, msg = set_shutdown_by_time(time_str)
        if success:
            self.check_existing_task()
        else:
            self.status_desc.configure(text=msg, text_color="#D9383A")

    def on_cancel(self):
        self.stop_thread_event.set()
        cancel_shutdown()
        self.active_task = None
        self.update_status_ui_idle()
        self.status_desc.configure(text="关机任务已取消 (Shutdown canceled)", text_color="gray")

    def destroy(self):
        self.stop_thread_event.set()
        super().destroy()

def parse_cli_args():
    """
    Parse command-line arguments.
    解析命令行参数。
    """
    parser = argparse.ArgumentParser(description="Windows 11 Scheduled Shutdown Utility / Windows 11 定时关机工具")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--delay", type=str, help="Shutdown after specified delay. E.g., 3600 (seconds) or 10m (10 minutes) or 2h (2 hours) / 在指定的延迟时间后关机。例如：3600（秒）、10m（10分钟）、2h（2小时）。")
    group.add_argument("-t", "--time", type=str, help="Shutdown at specified exact time. Format: HH:MM. E.g., 23:30 / 在指定的具体时刻关机。格式为 HH:MM，如 23:30。")
    group.add_argument("-c", "--cancel", action="store_true", help="Cancel any scheduled shutdown / 取消当前已设定的关机计划。")
    
    return parser.parse_args()

def parse_delay_str(delay_str):
    """
    Parse delay string (e.g. '10m', '2h', '3600') into hours and minutes.
    将延迟字符串（例如 '10m'，'2h'，'3600'）解析为小时与分钟。
    """
    delay_str = delay_str.lower().strip()
    if delay_str.endswith("s"):
        seconds = int(delay_str[:-1])
        return divmod(seconds, 3600)
    elif delay_str.endswith("m"):
        minutes = int(delay_str[:-1])
        return divmod(minutes * 60, 3600)
    elif delay_str.endswith("h"):
        hours = float(delay_str[:-1])
        total_minutes = int(hours * 60)
        return divmod(total_minutes * 60, 3600)
    else:
        # Assume raw seconds if no suffix is given
        # 若没有提供后缀，默认视为原始秒数
        try:
            seconds = int(delay_str)
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return h, m
        except ValueError:
            raise ValueError("Invalid delay format. E.g. 600, 10m, 2h / 无效的延迟格式。例如：600, 10m, 2h。")

def main():
    args = parse_cli_args()
    
    # CLI Mode Execution
    # 命令行模式执行
    if args.cancel:
        if cancel_shutdown():
            print("[INFO] Scheduled shutdown canceled successfully. / 已成功取消定时关机计划。")
        else:
            print("[INFO] No active scheduled shutdown to cancel or failed to cancel. / 当前无正在生效的定时关机计划，或取消失败。")
        sys.exit(0)
        
    elif args.delay:
        try:
            hours, minutes = parse_delay_str(args.delay)
            success, msg = set_shutdown_by_delay(hours, minutes)
            print(f"[CLI INFO] {msg}")
            if not success:
                sys.exit(1)
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
        sys.exit(0)
        
    elif args.time:
        success, msg = set_shutdown_by_time(args.time)
        print(f"[CLI INFO] {msg}")
        if not success:
            sys.exit(1)
        sys.exit(0)
        
    # GUI Mode Execution (if no arguments provided)
    # 图形界面模式执行（如果没有传入任何参数）
    else:
        app = ShutdownApp()
        app.mainloop()

if __name__ == "__main__":
    main()
