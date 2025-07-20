# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from api import TomatoAPI
import threading

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("番茄小说下载器")
        self.geometry("800x600")

        self.api = TomatoAPI()

        # --- Frames ---
        search_frame = ttk.LabelFrame(self, text="书籍搜索")
        search_frame.pack(padx=10, pady=5, fill="x")

        download_frame = ttk.LabelFrame(self, text="书籍下载")
        download_frame.pack(padx=10, pady=5, fill="x")

        log_frame = ttk.LabelFrame(self, text="日志")
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)

        # --- Search Widgets ---
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_books)
        search_button.pack(side="left", padx=5, pady=5)

        # --- Results TreeView ---
        self.tree = ttk.Treeview(self, columns=("ID", "Title", "Author"), show="headings")
        self.tree.heading("ID", text="Book ID")
        self.tree.heading("Title", text="书名")
        self.tree.heading("Author", text="作者")
        self.tree.pack(padx=10, pady=5, fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_tree_select)

        # --- Download Widgets ---
        self.book_id_var = tk.StringVar()
        id_label = ttk.Label(download_frame, text="Book ID:")
        id_label.pack(side="left", padx=5, pady=5)
        id_entry = ttk.Entry(download_frame, textvariable=self.book_id_var, width=50)
        id_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        download_button = ttk.Button(download_frame, text="下载", command=self.download_book)
        download_button.pack(side="left", padx=5, pady=5)

        # --- Log Widgets ---
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def search_books(self):
        keyword = self.search_var.get()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        
        self.log(f"正在搜索: {keyword}")
        threading.Thread(target=self._search_worker, args=(keyword,), daemon=True).start()

    def _search_worker(self, keyword):
        # Clear previous results
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        search_results = self.api.search(keyword)
        if search_results and 'data' in search_results:
            # 从API返回的数据结构中提取书籍信息
            books_found = 0
            for item in search_results['data']:
                if 'book_data' in item and len(item['book_data']) > 0:
                    book = item['book_data'][0]  # 取第一个书籍数据
                    self.tree.insert("", "end", values=(
                        book.get('book_id', 'N/A'), 
                        book.get('book_name', 'N/A'), 
                        book.get('author', 'N/A')
                    ))
                    books_found += 1
            
            if books_found > 0:
                self.log(f"找到 {books_found} 本相关书籍。")
            else:
                self.log("未找到相关书籍。")
                messagebox.showinfo("结果", "未找到相关书籍。")
        else:
            self.log("未找到相关书籍或发生错误。")
            messagebox.showinfo("结果", "未找到相关书籍。")

    def on_tree_select(self, event):
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            if values:
                book_id = values[0]  # 取第一个值，即book_id
                self.book_id_var.set(book_id)

    def download_book(self):
        book_id = self.book_id_var.get()
        if not book_id:
            messagebox.showwarning("警告", "请输入书籍ID")
            return
            
        self.log(f"准备下载书籍ID: {book_id}")
        threading.Thread(target=self._download_worker, args=(book_id,), daemon=True).start()
        
    def _download_worker(self, book_id):
        book_info = self.api.get_book_info(book_id)
        if not (book_info and 'data' in book_info):
            self.log(f"错误: 无法获取书籍信息 (ID: {book_id})")
            messagebox.showerror("错误", f"无法获取书籍信息 (ID: {book_id})")
            return

        book_data = book_info['data']
        book_name = book_data.get('book_name', f"book_{book_id}")
        self.log(f"书名: {book_name}")
        self.log(f"作者: {book_data.get('author')}")
        
        item_list = book_data.get('directory', {}).get('item_list', [])
        if not item_list:
            self.log("错误: 未找到章节列表。")
            messagebox.showerror("错误", "未找到章节列表。")
            return

        item_ids = [item['item_id'] for item in item_list]
        self.log(f"共找到 {len(item_ids)} 个章节。")

        full_content = ""
        item_id_chunks = [item_ids[i:i + 30] for i in range(0, len(item_ids), 30)]
        
        for i, chunk in enumerate(item_id_chunks):
            self.log(f"正在下载章节包 {i+1}/{len(item_id_chunks)}...")
            item_ids_str = ",".join(map(str, chunk))
            content_data = self.api.get_content(item_ids=item_ids_str, api_type='batch')
            if content_data and 'data' in content_data:
                for chapter_content in content_data['data']:
                    full_content += f"\n\n## {chapter_content.get('title', '')}\n\n"
                    full_content += chapter_content.get('content', '')
            else:
                self.log(f"警告: 无法下载章节包: {item_ids_str}")

        file_name = f"{book_name}.txt"
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(full_content)
            self.log(f"下载完成！书籍已保存为: {file_name}")
            messagebox.showinfo("成功", f"书籍已保存为: {file_name}")
        except IOError as e:
            self.log(f"错误: 无法保存文件: {e}")
            messagebox.showerror("错误", f"无法保存文件: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()