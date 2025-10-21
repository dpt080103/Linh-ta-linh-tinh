import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import sqlite3
import os
import datetime
import sys
import threading

# Tên của file CSDL SQLite
DATABASE_NAME = 'document_index.db'

# --- PHẦN BACKEND (XỬ LÝ CSDL) ---

def setup_database():
    """
    Tạo CSDL và bảng 'documents' nếu chúng chưa tồn tại.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            modified_date TIMESTAMP
        )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON documents (file_name)')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        # Hiển thị lỗi nghiêm trọng nếu không thể tạo CSDL
        messagebox.showerror("Lỗi CSDL", f"Không thể thiết lập CSDL: {e}")
        sys.exit(1)

def index_directory_task(directory_path, status_callback, completion_callback):
    """
    Tác vụ quét thư mục (để chạy trong một luồng riêng).
    """
    if not os.path.isdir(directory_path):
        completion_callback(False, f"Lỗi: Đường dẫn '{directory_path}' không tồn tại.")
        return

    try:
        status_callback("Bắt đầu kết nối CSDL...")
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        status_callback("Đang xóa chỉ mục cũ...")
        cursor.execute('DELETE FROM documents')
        conn.commit()

        status_callback(f"Đang quét thư mục: {directory_path}...")
        file_count = 0
        
        for root, dirs, files in os.walk(directory_path, topdown=True):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    mod_time_stamp = os.path.getmtime(file_path)
                    modified_date = datetime.datetime.fromtimestamp(mod_time_stamp)
                    
                    cursor.execute(
                        "INSERT INTO documents (file_name, file_path, modified_date) VALUES (?, ?, ?)",
                        (file, file_path, modified_date)
                    )
                    file_count += 1
                    
                    if file_count % 500 == 0:
                        # Cập nhật trạng thái
                        status_callback(f"Đã lập chỉ mục {file_count} file...")
                        
                except OSError:
                    # Bỏ qua file không thể truy cập
                    pass
        
        status_callback("Đang lưu thay đổi vào CSDL...")
        conn.commit()
        conn.close()
        
        completion_callback(True, f"Hoàn tất! Đã lập chỉ mục tổng cộng {file_count} file.")

    except sqlite3.Error as e:
        completion_callback(False, f"Lỗi CSDL: {e}")
    except Exception as e:
        completion_callback(False, f"Lỗi không xác định: {e}")

def search_documents_task(query):
    """
    Tìm kiếm tài liệu trong CSDL và trả về danh sách kết quả.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        search_term = f'%{query}%'
        
        cursor.execute(
            "SELECT file_name, file_path, modified_date FROM documents WHERE file_name LIKE ? ORDER BY modified_date DESC",
            (search_term,)
        )
        results = cursor.fetchall()
        conn.close()
        return results
    except sqlite3.Error as e:
        messagebox.showerror("Lỗi Tìm Kiếm", f"Lỗi khi truy vấn CSDL: {e}")
        return []

# --- PHẦN FRONTEND (GIAO DIỆN TKINTER) ---

class DocumentIndexerApp:
    def __init__(self, root):
        self.root = root
        root.title("Document Indexer")
        root.geometry("600x400")
        
        # Biến lưu trữ đường dẫn thư mục đã chọn
        self.directory_to_index = tk.StringVar()

        # Tạo các tab
        self.tab_control = ttk.Notebook(root)
        
        self.tab_index = ttk.Frame(self.tab_control, padding="10")
        self.tab_search = ttk.Frame(self.tab_control, padding="10")
        
        self.tab_control.add(self.tab_index, text='Lập Chỉ mục')
        self.tab_control.add(self.tab_search, text='Tìm Kiếm')
        self.tab_control.pack(expand=1, fill="both")
        
        # --- Cấu hình Tab 1: Lập Chỉ mục ---
        self.setup_index_tab()
        
        # --- Cấu hình Tab 2: Tìm Kiếm ---
        self.setup_search_tab()

    def setup_index_tab(self):
        # Frame chứa phần chọn thư mục
        frame_select = ttk.Frame(self.tab_index)
        frame_select.pack(fill="x", pady=5)

        lbl_select = ttk.Label(frame_select, text="Thư mục cần quét:")
        lbl_select.pack(side=tk.LEFT, padx=5)
        
        entry_path = ttk.Entry(frame_select, textvariable=self.directory_to_index, width=50, state="readonly")
        entry_path.pack(side=tk.LEFT, expand=True, fill="x", padx=5)
        
        btn_browse = ttk.Button(frame_select, text="...", width=4, command=self.browse_directory)
        btn_browse.pack(side=tk.LEFT)

        # Nút bắt đầu
        self.btn_start_index = ttk.Button(self.tab_index, text="Bắt đầu Lập Chỉ mục", command=self.start_indexing_thread)
        self.btn_start_index.pack(pady=10)

        # Label hiển thị trạng thái
        self.lbl_index_status = ttk.Label(self.tab_index, text="Trạng thái: Sẵn sàng.")
        self.lbl_index_status.pack(pady=5)
        
    def setup_search_tab(self):
        # Frame chứa phần tìm kiếm
        frame_search = ttk.Frame(self.tab_search)
        frame_search.pack(fill="x", pady=5)

        lbl_search = ttk.Label(frame_search, text="Nhập từ khóa:")
        lbl_search.pack(side=tk.LEFT, padx=5)
        
        self.entry_query = ttk.Entry(frame_search, width=50)
        self.entry_query.pack(side=tk.LEFT, expand=True, fill="x", padx=5)
        # Bắt sự kiện nhấn phím Enter
        self.entry_query.bind("<Return>", self.perform_search)
        
        btn_search = ttk.Button(frame_search, text="Tìm", command=self.perform_search)
        btn_search.pack(side=tk.LEFT)

        # Khung kết quả (ScrolledText)
        self.txt_results = scrolledtext.ScrolledText(self.tab_search, wrap=tk.WORD, height=15, state="disabled")
        self.txt_results.pack(expand=True, fill="both", pady=10)
        
    def browse_directory(self):
        """Mở hộp thoại chọn thư mục."""
        path = filedialog.askdirectory()
        if path:
            self.directory_to_index.set(path)
            self.lbl_index_status.config(text=f"Đã chọn: {path}")

    def start_indexing_thread(self):
        """
        Bắt đầu tác vụ index trong một luồng (thread) riêng 
        để tránh làm đơ giao diện.
        """
        path = self.directory_to_index.get()
        if not path:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một thư mục để lập chỉ mục.")
            return
            
        # Vô hiệu hóa nút để tránh chạy nhiều lần
        self.btn_start_index.config(state="disabled")
        self.lbl_index_status.config(text="Đang bắt đầu...")
        
        # Tạo và bắt đầu luồng
        # Chúng ta truyền các hàm callback để luồng có thể cập nhật GUI
        # một cách an toàn (thông qua .after())
        index_thread = threading.Thread(
            target=index_directory_task,
            args=(
                path, 
                self.update_status_safe, 
                self.on_indexing_complete_safe
            ),
            daemon=True # Thoát luồng khi đóng chương trình chính
        )
        index_thread.start()

    def update_status_safe(self, message):
        """Hàm an toàn để cập nhật label trạng thái từ luồng khác."""
        # root.after(0, ...) sẽ lên lịch chạy hàm này trên luồng GUI chính
        self.root.after(0, self.lbl_index_status.config, {"text": message})

    def on_indexing_complete_safe(self, success, message):
        """Hàm an toàn để gọi khi luồng index hoàn tất."""
        self.root.after(0, self.on_indexing_complete, success, message)

    def on_indexing_complete(self, success, message):
        """Chạy trên luồng GUI khi index xong."""
        if success:
            messagebox.showinfo("Hoàn tất", message)
            self.lbl_index_status.config(text="Trạng thái: Sẵn sàng.")
        else:
            messagebox.showerror("Lỗi", message)
            self.lbl_index_status.config(text="Trạng thái: Có lỗi xảy ra.")
        
        # Kích hoạt lại nút
        self.btn_start_index.config(state="normal")
        
    def perform_search(self, event=None): # Thêm event=None để bắt sự kiện Enter
        """Thực hiện tìm kiếm và hiển thị kết quả."""
        query = self.entry_query.get()
        if not query:
            messagebox.showwarning("Thiếu từ khóa", "Vui lòng nhập từ khóa tìm kiếm.")
            return

        results = search_documents_task(query)
        
        # Cho phép chỉnh sửa Text để chèn kết quả
        self.txt_results.config(state="normal")
        self.txt_results.delete(1.0, tk.END) # Xóa kết quả cũ
        
        if not results:
            self.txt_results.insert(tk.END, f"Không tìm thấy kết quả nào cho '{query}'.")
        else:
            self.txt_results.insert(tk.END, f"--- Tìm thấy {len(results)} kết quả cho '{query}' ---\n\n")
            for i, (name, path, mod_date) in enumerate(results, 1):
                self.txt_results.insert(tk.END, f"Kết quả {i}:\n")
                self.txt_results.insert(tk.END, f"  📁 Tên file: {name}\n")
                self.txt_results.insert(tk.END, f"  📍 Đường dẫn: {path}\n")
                self.txt_results.insert(tk.END, f"  📅 Ngày sửa: {mod_date}\n")
                self.txt_results.insert(tk.END, "-"*20 + "\n")
        
        # Khóa Text lại (chỉ đọc)
        self.txt_results.config(state="disabled")

# --- Điểm bắt đầu của chương trình ---
if __name__ == "__main__":
    # 1. Đảm bảo CSDL được thiết lập trước khi chạy GUI
    setup_database()
    
    # 2. Tạo cửa sổ chính và chạy ứng dụng
    main_window = tk.Tk()
    app = DocumentIndexerApp(main_window)
    main_window.mainloop()