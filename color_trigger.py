import tkinter as tk
import pyautogui
import threading
import time
from tkinter import colorchooser
import configparser
import os

class ColorTriggerTool:
    def __init__(self):
        # 主窗口
        self.root = tk.Tk()
        self.root.title('Color Trigger Tool')
        self.root.geometry('300x200')
        
        # 设置窗口置顶
        self.root.attributes('-topmost', 1)
        
        # 初始化配置
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        
        # 加载配置
        self.load_config()
        
        # 状态变量
        self.running = False
        self.trigger_color = self.hex_to_rgb(self.config.get('Settings', 'last_color', fallback='#ff0000'))  # 默认红色
        
        # 窗口引用（必须优先初始化）
        self.crosshair_window = None  # 确保最先初始化的属性
        
        # 监控线程引用
        self.monitor_thread = None
        
        # 初始化坐标相关属性
        self.trigger_x = 0  # 颜色监测坐标
        self.trigger_y = 0
        self.click_x = 0    # 点击坐标
        self.click_y = 0
        self.position_set = False
        self.saved_position = None  # 添加缺失的属性初始化
        self.window_pos = None      # 添加缺失的属性初始化
        
        # 添加窗口状态事件
        self.window_created = threading.Event()
        self.window_visible = False  # 窗口可见性状态
        
        # 创建界面
        self.create_widgets()
        
        # 启动主循环
        self.root.mainloop()

    def create_widgets(self):
        # 状态标签
        self.status_label = tk.Label(self.root, text='Status: Waiting', fg='green')
        self.status_label.pack(pady=10)
        
        # 按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # 设置触发坐标按钮
        self.set_trigger_button = tk.Button(button_frame, text='Set Trigger Position', command=self.set_trigger_position)
        self.set_trigger_button.pack(side='left', padx=5)
        
        # 设置点击坐标按钮
        self.set_click_button = tk.Button(button_frame, text='Set Click Position', command=self.set_click_position)
        self.set_click_button.pack(side='left', padx=5)
        
        # 启动/停止按钮框架
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        # 启动按钮
        self.start_button = tk.Button(control_frame, text='Start (Ctrl+S)', command=self.start_monitoring)
        self.start_button.pack(side='left', padx=5)
        
        # 停止按钮
        self.stop_button = tk.Button(control_frame, text='Stop (Ctrl+Q)', command=self.stop_monitoring)
        self.stop_button.pack(side='left', padx=5)
        
        # 快捷键绑定
        self.root.bind('<Control-s>', lambda e: self.start_monitoring())
        self.root.bind('<Control-S>', lambda e: self.start_monitoring())
        self.root.bind('<Control-q>', lambda e: self.stop_monitoring())
        self.root.bind('<Control-Q>', lambda e: self.stop_monitoring())

    def load_config(self):
        """加载配置文件，若不存在则创建默认配置"""
        # 检查配置文件是否存在
        if not os.path.exists(self.config_file):
            # 创建默认配置
            self.config['Settings'] = {
                'last_color': '#ff0000',  # 默认红色
                'position': 'center'      # 默认居中显示
            }
            try:
                # 写入默认配置文件
                with open(self.config_file, 'w') as configfile:
                    self.config.write(configfile)
                print(f"[配置] 创建默认配置文件: {self.config_file}")
            except Exception as e:
                print(f"[配置] 创建配置文件失败: {e}")
                return
        
        # 读取现有配置
        try:
            self.config.read(self.config_file)
            print(f"[配置] 成功加载配置文件: {self.config_file}")
            
            # 加载独立坐标
            if 'Settings' in self.config:
                # 加载触发坐标
                if 'trigger_position' in self.config['Settings']:
                    try:
                        x, y = map(int, self.config['Settings']['trigger_position'].split(','))
                        self.trigger_x = x
                        self.trigger_y = y
                    except Exception as e:
                        print(f"[配置] 触发坐标加载失败: {e}")
                
                # 加载点击坐标
                if 'click_position' in self.config['Settings']:
                    try:
                        x, y = map(int, self.config['Settings']['click_position'].split(','))
                        self.click_x = x
                        self.click_y = y
                    except Exception as e:
                        print(f"[配置] 点击坐标加载失败: {e}")
            
            # 更新坐标有效性状态
            if self.trigger_x > 0 and self.trigger_y > 0 and self.click_x > 0 and self.click_y > 0:
                self.position_set = True
                print("[配置] 成功加载有效坐标")
            else:
                self.position_set = False
                print("[配置] 坐标未设置或无效")
            
        except Exception as e:
            print(f"[配置] 读取配置文件失败: {e}")
            # 创建默认配置作为后备方案
            self.config['Settings'] = {'last_color': '#ff0000'}

    def create_crosshair_window(self):
        # 销毁现有窗口（如果存在）
        print("[窗口操作] 创建十字光标窗口")
        # 修改条件判断方式，避免直接访问未定义属性
        if hasattr(self, 'crosshair_window') and self.crosshair_window:
            try:
                print("[窗口操作] 发现旧窗口，正在销毁...")
                self.crosshair_window.destroy()
            finally:
                self.crosshair_window = None
                print("[窗口操作] 旧窗口已销毁")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口位置
        window_width = 200
        window_height = 200
        
        # 使用保存的位置或居中
        # 添加属性存在性检查
        if self.window_pos and isinstance(self.window_pos, (list, tuple)) and len(self.window_pos) >= 2:
            x, y = self.window_pos[:2]
        else:
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
        
        # 创建十字光标窗口
        try:
            # 添加模式提示
            if hasattr(self, 'position_mode'):
                if self.position_mode == 'trigger':
                    window_title = 'Select Trigger Position'
                elif self.position_mode == 'click':
                    window_title = 'Select Click Position'
                else:
                    window_title = 'Select Position'
            else:
                window_title = 'Select Position'
            
            # 创建窗口
            self.crosshair_window = tk.Toplevel()
            self.crosshair_window.title(window_title)
            self.crosshair_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
            
            # 设置窗口属性
            self.crosshair_window.attributes('-topmost', 1)  # 置顶
            self.crosshair_window.resizable(False, False)  # 不可缩放
            self.crosshair_window.configure(bg='black')  # 黑色背景
            self.crosshair_window.attributes('-alpha', 0.3)  # 半透明
            self.crosshair_window.overrideredirect(True)  # 无边框
            
            # 添加十字光标
            self.canvas = tk.Canvas(self.crosshair_window, bg='black', highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            
            # 绑定鼠标事件
            self.crosshair_window.bind('<B1-Motion>', self.move_window)  # 拖动
            self.crosshair_window.bind('<Double-Button-1>', self.confirm_position)  # 双击确认
            
            # 初始绘制十字光标
            self.crosshair_window.update()
            print(f"[窗口操作] 十字光标窗口已创建 @ ({x}, {y})")
            print(f"[窗口操作] 窗口winfo_exists: {self.crosshair_window.winfo_exists()}")
            print(f"[窗口操作] 窗口winfo_viewable: {self.crosshair_window.winfo_viewable()}")
            print(f"[窗口操作] 窗口状态: {self.crosshair_window.state()}")
            
            # 初始绘制十字光标
            self.draw_crosshair()
            
            # 绑定窗口配置事件
            self.crosshair_window.bind('<Configure>', self.on_window_configure)
            
            # 设置窗口创建事件
            self.window_created.set()
            self.window_visible = True  # 设置可见性状态
            
            # 添加窗口创建完成日志
            print("[窗口操作] 十字光标窗口创建完成")
            print(f"[窗口操作] 窗口引用地址: {id(self.crosshair_window)}")
            print(f"[窗口操作] 窗口事件状态: {self.window_created.is_set()}")
        except Exception as e:
            print(f"[窗口操作] 创建十字光标窗口失败: {e}")

    def on_window_configure(self, event=None):
        # 窗口配置变化时重绘十字光标
        if event and 'width' in event.widget.winfo_geometry():
            print(f"[窗口操作] 窗口配置变化: {event.widget.winfo_geometry()}")
            self.draw_crosshair()
    
    def draw_crosshair(self):
        # 清除之前的绘制
        self.canvas.delete('all')
        
        # 获取画布尺寸
        canvas_width = self.canvas.winfo_width() or 200
        canvas_height = self.canvas.winfo_height() or 200
        
        # 计算中心点
        self.center_x = canvas_width // 2
        self.center_y = canvas_height // 2
        
        # 绘制十字光标
        self.canvas.create_line(
            0, self.center_y,
            canvas_width, self.center_y,
            fill='white', width=1
        )
        self.canvas.create_line(
            self.center_x, 0,
            self.center_x, canvas_height,
            fill='white', width=1
        )
        
        # 绘制中心点
        self.canvas.create_oval(
            self.center_x - 2, self.center_y - 2,
            self.center_x + 2, self.center_y + 2,
            fill='white'
        )
        
        # 添加调试信息
        print(f"[十字光标] 重绘十字光标 - 画布尺寸: {canvas_width}x{canvas_height}")
        print(f"[十字光标] 中心点: ({self.center_x}, {self.center_y})")
    
    def move_window(self, event):
        # 拖动窗口
        if not self.crosshair_window:
            return
        
        # 获取窗口实际尺寸
        window_width = self.crosshair_window.winfo_width() or 200
        window_height = self.crosshair_window.winfo_height() or 200
        
        # 计算新位置
        x = event.x_root - window_width // 2
        y = event.y_root - window_height // 2
        
        # 移动窗口
        self.crosshair_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # 添加调试信息
        print(f"[窗口操作] 窗口拖动 @ ({x}, {y})")
        print(f"[窗口操作] 窗口位置: {self.crosshair_window.geometry()}")
    
    def confirm_position(self, event=None):
        # 确认位置
        if not self.crosshair_window:
            return
        
        # 保存配置
        self.save_config()
        
        # 保存位置
        try:
            # 获取窗口位置
            pos_x = self.crosshair_window.winfo_rootx()
            pos_y = self.crosshair_window.winfo_rooty()
            # 保存窗口位置和尺寸
            self.saved_position = (
                pos_x,
                pos_y,
                self.crosshair_window.winfo_width(),
                self.crosshair_window.winfo_height()
            )
            # 根据模式保存不同坐标
            if hasattr(self, 'position_mode'):
                if self.position_mode == 'trigger':
                    self.trigger_x = pos_x + self.center_x
                    self.trigger_y = pos_y + self.center_y
                    print(f"[坐标管理] 触发坐标已保存: ({self.trigger_x}, {self.trigger_y})")
                elif self.position_mode == 'click':
                    self.click_x = pos_x + self.center_x
                    self.click_y = pos_y + self.center_y
                    print(f"[坐标管理] 点击坐标已保存: ({self.click_x}, {self.click_y})")
                else:  # 默认模式（兼容旧逻辑）
                    self.trigger_x = pos_x + self.center_x
                    self.trigger_y = pos_y + self.center_y
                    self.click_x = pos_x + self.center_x
                    self.click_y = pos_y + self.center_y
                    self.position_set = True
                    print(f"[坐标管理] 坐标已保存: 触发坐标({self.trigger_x}, {self.trigger_y}), 点击坐标({self.click_x}, {self.click_y})")
            
        except Exception as e:
            print(f"[窗口操作] 窗口位置获取失败: {e}")
            # 重置所有坐标
            self.trigger_x = 0
            self.trigger_y = 0
            self.click_x = 0
            self.click_y = 0
            self.position_set = False
        
        # 销毁窗口
        try:
            self.crosshair_window.destroy()
        finally:
            # 清除窗口引用
            self.crosshair_window = None
            print("[窗口操作] 窗口已销毁")
            # 窗口销毁后主动停止监控（如果正在运行）
            if self.running:
                print("[窗口操作] 窗口销毁后主动停止监控")
                self.stop_monitoring()
        
        # 更新状态
        self.root.title(f'Color Trigger Tool - 已确认位置')
        self.status_label.config(text='Status: 已确认位置', fg='blue')
    
    def choose_color(self):
        # 选择触发颜色
        try:
            # 将RGB转换为十六进制
            tk_color = self.rgb_to_hex(self.trigger_color)
        except Exception:
            tk_color = '#ff0000'  # 默认红色
            self.trigger_color = (255, 0, 0)
        
        # 选择触发颜色
        selected_color = colorchooser.askcolor(color=tk_color, title='Choose Trigger Color')
        if selected_color[0]:
            # 保存颜色
            self.trigger_color = tuple(map(int, selected_color[0]))
            print(f"Trigger color set to: {self.trigger_color}")
            # 更新状态标签
            self.status_label.config(text=f'Trigger Color: {self.trigger_color}', fg='blue')
    
    def start_monitoring(self):
        # 启动监控
        if not self.position_set:
            print("[监控控制] 错误: 坐标未设置")
            self.status_label.config(text='错误: 坐标未设置', fg='red')
            return
        
        # 启动监控
        if not self.running:
            print("[线程管理] 准备启动监控线程...")
            self.running = True
            self.status_label.config(text='Status: Monitoring', fg='red')
            
            # 添加线程安全检查
            if self.monitor_thread and self.monitor_thread.is_alive():
                print("[线程管理] 监控线程仍在运行，等待其结束...")
                self.monitor_thread.join()
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self.monitor_color)
            self.monitor_thread.start()
            print("[线程管理] 监控线程已启动")
    
    def stop_monitoring(self):
        # 停止监控
        if self.running:
            print("[线程管理] 准备停止监控线程...")
            self.running = False
            self.status_label.config(text='Status: Waiting', fg='green')
            
            # 添加线程安全检查
            if self.monitor_thread and self.monitor_thread.is_alive():
                print("[线程管理] 监控线程仍在运行，等待其结束...")
                self.monitor_thread.join()
            print("[线程管理] 监控线程已停止")
    
    def monitor_color(self):
        # 颜色监控线程
        try:
            # 线程初始化
            print("[监控线程] 线程启动成功")
            print("[监控线程] 开始监控循环...")
            while self.running:
                # 获取屏幕坐标
                try:
                    print(f"[监控线程] 当前坐标 - 触发点: ({self.trigger_x}, {self.trigger_y}), 点击点: ({self.click_x}, {self.click_y})")
                except Exception as e:
                    print(f"[监控线程] 坐标获取失败: {e}")
                    continue
                
                # 获取屏幕像素颜色
                try:
                    # 使用触发坐标获取颜色
                    pixel_color = pyautogui.pixel(self.trigger_x, self.trigger_y)
                    print(f"[监控线程] 当前颜色 - 位置: ({self.trigger_x}, {self.trigger_y}), 颜色: {pixel_color}")
                except Exception as e:
                    print(f"[监控线程] Pixel获取错误: {e}")
                    continue
                
                # 检查颜色是否匹配
                if self.color_match(pixel_color, self.trigger_color):
                    # 执行鼠标点击
                    try:
                        # 使用点击坐标进行点击
                        pyautogui.click(self.click_x, self.click_y)
                        print(f"[监控线程] 颜色匹配！点击执行于 ({self.click_x}, {self.click_y})")
                    except Exception as e:
                        print(f"[监控线程] 点击执行错误: {e}")
                        # 添加详细错误信息
                        import traceback
                        print(f"[监控线程] 错误追踪: {traceback.format_exc()}")
                
                # 检测间隔（0.1秒）
                time.sleep(0.1)
        except Exception as e:
            print(f"[监控线程] 严重错误: {e}")
            # 添加错误类型信息
            print(f"[监控线程] 错误类型: {type(e).__name__}")
            self.status_label.config(text='错误: 点击执行失败', fg='red')
        finally:
            self.running = False
            print("[监控线程] 线程已终止")
    
    def save_config(self):
        # 保存配置文件
        try:
            # 保存颜色配置
            self.config['Settings'] = {
                'last_color': self.rgb_to_hex(self.trigger_color)
            }
            
            # 保存独立坐标
            if hasattr(self, 'trigger_x') and hasattr(self, 'trigger_y'):
                self.config['Settings']['trigger_position'] = f"{self.trigger_x},{self.trigger_y}"
            if hasattr(self, 'click_x') and hasattr(self, 'click_y'):
                self.config['Settings']['click_position'] = f"{self.click_x},{self.click_y}"
            
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"配置保存失败: {e}")
    
    def hex_to_rgb(self, hex_color):
        # 将十六进制颜色转换为RGB元组
        return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    
    def rgb_to_hex(self, rgb_color):
        # 将RGB元组转换为十六进制颜色
        return '#{:02x}{:02x}{:02x}'.format(*rgb_color)
    
    def color_match(self, color1, color2, threshold=5):
        # 检查颜色是否匹配（允许一定差异）
        # 如果是十六进制字符串，转换为RGB
        if isinstance(color2, str):
            try:
                color2 = self.hex_to_rgb(color2)
            except ValueError:
                color2 = (255, 0, 0)  # 默认红色
        
        # 记录颜色匹配检查
        print(f"[颜色匹配] 比较颜色 - 当前: {color1}, 目标: {color2}, 差异阈值: {threshold}")
        print(f"[颜色匹配] 各通道差异 - R: {abs(color1[0] - color2[0])}, G: {abs(color1[1] - color2[1])}, B: {abs(color1[2] - color2[2])}")
        
        return all(abs(c1 - c2) <= threshold for c1, c2 in zip(color1, color2))

    def set_trigger_position(self):
        # 设置触发坐标
        print("[坐标设置] 开始设置触发坐标...")
        self.position_mode = 'trigger'  # 添加模式标志
        self.create_crosshair_window()

    def set_click_position(self):
        # 设置点击坐标
        print("[坐标设置] 开始设置点击坐标...")
        self.position_mode = 'click'  # 添加模式标志
        self.create_crosshair_window()

if __name__ == '__main__':
    ColorTriggerTool()
