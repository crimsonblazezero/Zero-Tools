import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
# 导入拖拽库
from tkinterdnd2 import TkinterDnD, DND_FILES

class DragDropCopyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多文件分发工具 (支持批量拖拽)")
        self.root.geometry("750x650")
        
        # ================= 1. 源文件区域 =================
        tk.Label(root, text="第一步：添加需要复制的源文件 (支持直接拖拽文件到下方)", font=("微软雅黑", 10, "bold")).pack(pady=(10, 0))
        file_btn_frame = tk.Frame(root)
        file_btn_frame.pack(pady=5)
        tk.Button(file_btn_frame, text="+ 浏览文件", command=self.add_files, bg="#e0f7fa").grid(row=0, column=0, padx=5)
        tk.Button(file_btn_frame, text="移除选中", command=lambda: self.remove_selected(self.file_listbox)).grid(row=0, column=1, padx=5)
        tk.Button(file_btn_frame, text="清空", command=lambda: self.file_listbox.delete(0, tk.END)).grid(row=0, column=2, padx=5)

        file_list_frame = tk.Frame(root)
        file_list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        file_scroll = tk.Scrollbar(file_list_frame)
        file_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox = tk.Listbox(file_list_frame, selectmode=tk.MULTIPLE, yscrollcommand=file_scroll.set, height=8, bg="#f8f9fa")
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scroll.config(command=self.file_listbox.yview)

        # 注册拖拽事件：源文件
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.drop_files)

        # ================= 2. 目标文件夹区域 =================
        tk.Label(root, text="第二步：添加目标文件夹 (支持直接框选多个文件夹拖拽到下方)", font=("微软雅黑", 10, "bold"), fg="#d32f2f").pack(pady=(15, 0))
        dir_btn_frame = tk.Frame(root)
        dir_btn_frame.pack(pady=5)
        tk.Button(dir_btn_frame, text="+ 浏览文件夹", command=self.add_dest_folder, bg="#fff9c4").grid(row=0, column=0, padx=5)
        tk.Button(dir_btn_frame, text="移除选中", command=lambda: self.remove_selected(self.dir_listbox)).grid(row=0, column=1, padx=5)
        tk.Button(dir_btn_frame, text="清空", command=lambda: self.dir_listbox.delete(0, tk.END)).grid(row=0, column=2, padx=5)

        dir_list_frame = tk.Frame(root)
        dir_list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        dir_scroll = tk.Scrollbar(dir_list_frame)
        dir_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.dir_listbox = tk.Listbox(dir_list_frame, selectmode=tk.MULTIPLE, yscrollcommand=dir_scroll.set, height=8, bg="#fffde7")
        self.dir_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dir_scroll.config(command=self.dir_listbox.yview)

        # 注册拖拽事件：目标文件夹
        self.dir_listbox.drop_target_register(DND_FILES)
        self.dir_listbox.dnd_bind('<<Drop>>', self.drop_folders)

        # ================= 3. 执行区域 =================
        exec_frame = tk.Frame(root)
        exec_frame.pack(pady=15)
        tk.Button(exec_frame, text="第三步：开始批量分发", command=self.execute_copy, bg="#c8e6c9", font=("微软雅黑", 12, "bold"), width=20, height=2).pack()

    # --- 拖拽处理逻辑 ---
    def drop_files(self, event):
        # 使用 splitlist 解决路径中带空格导致的解析错误坑
        files = self.root.tk.splitlist(event.data)
        for f in files:
            # 确保拖入的是文件，且未在列表中
            if os.path.isfile(f) and f not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, f)

    def drop_folders(self, event):
        folders = self.root.tk.splitlist(event.data)
        for d in folders:
            # 确保拖入的是文件夹，且未在列表中
            if os.path.isdir(d) and d not in self.dir_listbox.get(0, tk.END):
                self.dir_listbox.insert(tk.END, d)

    # --- 常规按钮逻辑 ---
    def add_files(self):
        files = filedialog.askopenfilenames(title="选择源文件")
        for f in files:
            if f not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, f)

    def add_dest_folder(self):
        folder = filedialog.askdirectory(title="选择目标文件夹")
        if folder and folder not in self.dir_listbox.get(0, tk.END):
            self.dir_listbox.insert(tk.END, folder)

    def remove_selected(self, listbox):
        selected_indices = listbox.curselection()
        for i in reversed(selected_indices):
            listbox.delete(i)

    def execute_copy(self):
        source_files = self.file_listbox.get(0, tk.END)
        dest_folders = self.dir_listbox.get(0, tk.END)

        if not source_files:
            messagebox.showwarning("提示", "源文件列表为空，请先添加文件！")
            return
        if not dest_folders:
            messagebox.showwarning("提示", "目标文件夹列表为空，请先添加目标路径！")
            return

        success_count = 0
        total_tasks = len(source_files) * len(dest_folders)

        for src in source_files:
            for dest in dest_folders:
                try:
                    shutil.copy2(src, dest)
                    success_count += 1
                except Exception as e:
                    messagebox.showerror("错误", f"复制文件出错\n文件: {src}\n目标: {dest}\n原因: {str(e)}")
                    return
        
        messagebox.showinfo("任务完成", f"分发完成！\n总计划复制：{total_tasks} 次\n成功复制：{success_count} 次")

if __name__ == "__main__":
    # 注意：使用拖拽功能必须用 TkinterDnD.Tk() 替代原来的 tk.Tk()
    root = TkinterDnD.Tk()
    app = DragDropCopyApp(root)
    root.mainloop()