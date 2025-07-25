import tkinter as tk
import pyautogui

class CoordinatePicker:
    def __init__(self):
        # 主控制窗口
        self.root = tk.Tk()
        self.root.title('Coordinate Picker')
        self.root.geometry('300x200')
        
        # 设置控制窗口置顶
        self.root.attributes('-topmost', 1)
        
        # 坐标输入框
        self.x_label = tk.Label(self.root, text='X Coordinate:')
        self.x_label.pack()
        self.x_entry = tk.Entry(self.root)
        self.x_entry.pack()
        
        self.y_label = tk.Label(self.root, text='Y Coordinate:')
        self.y_label.pack()
        self.y_entry = tk.Entry(self.root)
        self.y_entry.pack()
        
        # 按钮框架（使用frame布局）
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        # 坐标选择按钮
        self.pick_button = tk.Button(button_frame, text='Pick Coordinate', command=self.show_crosshair)
        self.pick_button.pack(side='left', padx=5)
        
        # 模拟点击按钮
        self.click_button = tk.Button(button_frame, text='Simulate Double Click', command=self.simulate_click)
        self.click_button.pack(side='left', padx=5)
        
        # 启动主循环
        self.root.mainloop()
    
    def show_crosshair(self):
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口居中位置
        window_width = 300  # 修改为300x300
        window_height = 300
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 创建可移动的红框窗口
        cross_window = tk.Toplevel(self.root)
        cross_window.title('Crosshair Window')  # 添加标题
        cross_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # 设置窗口置顶
        cross_window.attributes('-topmost', 1)
        # 设置窗口不可缩放
        cross_window.resizable(False, False)  # 禁用缩放
        # 设置窗口背景为半透明红色（保留窗口装饰）
        cross_window.configure(bg='red')
        cross_window.attributes('-alpha', 0.5)
        
        # 添加十字准心
        canvas = tk.Canvas(cross_window, bg='red', highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        # 绘制十字准心（基于窗口尺寸）
        canvas.create_line(0, window_height // 2, window_width, window_height // 2, fill='black')
        canvas.create_line(window_width // 2, 0, window_width // 2, window_height, fill='black')
        
        # 创建事件绑定函数
        def on_canvas_double_click(event):
            # 获取红框窗口在屏幕上的绝对位置
            win_x = cross_window.winfo_rootx()
            win_y = cross_window.winfo_rooty()
            
            # 获取十字准心在窗口中的位置
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            # 计算中心坐标（使用屏幕绝对坐标）
            center_x = win_x + canvas_width // 2
            center_y = win_y + canvas_height // 2
            
            # 更新输入框
            self.x_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(center_x))
            self.y_entry.delete(0, tk.END)
            self.y_entry.insert(0, str(center_y))
            
            # 解除事件绑定
            canvas.unbind('<Double-Button-1>')
            cross_window.unbind('<B1-Motion>')
            
            # 销毁红框窗口
            cross_window.destroy()
        
        def move_window(event):
            # 拖动窗口
            x = event.x_root - window_width // 2  # 使用动态计算的窗口宽度
            y = event.y_root - window_height // 2  # 使用动态计算的窗口高度
            cross_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # 绑定鼠标事件
        canvas.bind('<Double-Button-1>', on_canvas_double_click)
        cross_window.bind('<B1-Motion>', move_window)
    
    def simulate_click(self):
        # 获取输入框坐标
        try:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            # 执行双击操作
            pyautogui.moveTo(x, y)
            pyautogui.doubleClick()
            print(f"Double click executed at ({x}, {y})")
        except ValueError:
            print("请输入有效的坐标数值")

# 运行程序
if __name__ == '__main__':
    CoordinatePicker()