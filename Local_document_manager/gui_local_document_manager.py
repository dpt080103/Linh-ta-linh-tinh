import os
import datetime
from tkinter import *
from tkinter import messagebox

# --- CẤU HÌNH VÀ THIẾT LẬP THƯ MỤC GỐC ---
# Tài liệu sẽ được lưu trong thư mục TaiLieuHocTap_App trong thư mục người dùng của bạn.
BASE_DIR = os.path.join(os.path.expanduser("~"), "TaiLieuHocTap_App")


def save_document_locally(subject: str, topic: str, doc_name: str, content: str) -> str:
    """
    Tạo cấu trúc thư mục và lưu nội dung tài liệu vào một tệp tin cục bộ.
    Trả về thông báo kết quả.
    """
    if not subject or not topic or not doc_name or not content:
        return "LỖI: Vui lòng điền đầy đủ tất cả các trường thông tin."

    try:
        # 1. Định dạng Tên Tệp và Đường dẫn
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Loại bỏ các ký tự không hợp lệ cho tên thư mục và tệp
        subject_dir = subject.replace('/', '-').replace('\\', '-').strip()
        topic_dir = topic.replace('/', '-').replace('\\', '-').strip()
        doc_name_clean = doc_name.replace('/', '-').replace('\\', '-').strip()
        
        file_name = f"{doc_name_clean}_{today_date}.txt"
        
        target_dir = os.path.join(BASE_DIR, subject_dir, topic_dir)
        target_filepath = os.path.join(target_dir, file_name)

        # 2. Tạo Thư mục nếu chưa tồn tại (Hành động "Tạo thư mục" theo yêu cầu)
        os.makedirs(target_dir, exist_ok=True)

        # 3. Lưu Nội dung vào Tệp tin
        with open(target_filepath, 'w', encoding='utf-8') as f:
            f.write(f"--- MÔN HỌC: {subject} ---\n")
            f.write(f"--- CHỦ ĐỀ: {topic} ---\n")
            f.write(f"--- TÊN TÀI LIỆU: {doc_name} ---\n\n")
            f.write("----------------------------------------\n\n")
            f.write(content)
        
        return f"THÀNH CÔNG: Đã lưu tài liệu tại:\n{target_filepath}"

    except Exception as e:
        return f"LỖI: Không thể lưu tài liệu. Chi tiết lỗi: {e}"


# --- GIAO DIỆN NGƯỜI DÙNG (GUI) ---

class DocumentManagerApp:
    def __init__(self, master):
        self.master = master
        master.title("Quản Lý Tài Liệu Học Tập Cục Bộ")
        if os.path.exists("app_icon.ico"):
            master.iconbitmap("app_icon.ico")
        else:
            print("Không tìm thấy tệp 'app_icon.ico'. Icon sẽ không được hiển thị.")
        master.configure(padx=15, pady=15, background='#f0f0f0')

        # Thiết lập các biến cho Entry fields
        self.subject_var = StringVar()
        self.topic_var = StringVar()
        self.doc_name_var = StringVar()

        # Tiêu đề ứng dụng
        title_label = Label(master, text="HỆ THỐNG LƯU TRỮ TÀI LIỆU HỌC TẬP", 
                            font=("Arial", 16, "bold"), fg="#1e3a8a", bg='#f0f0f0', pady=10)
        title_label.grid(row=0, column=0, columnspan=2, sticky="ew")

        # --- Các trường nhập liệu ---
        current_row = 1
        
        # Môn Học
        Label(master, text="1. Môn Học:", font=("Arial", 10, "bold"), bg='#f0f0f0').grid(row=current_row, column=0, sticky="w", pady=5)
        Entry(master, textvariable=self.subject_var, width=50, bd=2, relief="groove").grid(row=current_row, column=1, sticky="ew", padx=10, pady=5)
        current_row += 1
        
        # Chủ Đề (Mục)
        Label(master, text="2. Chủ Đề/Mục:", font=("Arial", 10, "bold"), bg='#f0f0f0').grid(row=current_row, column=0, sticky="w", pady=5)
        Entry(master, textvariable=self.topic_var, width=50, bd=2, relief="groove").grid(row=current_row, column=1, sticky="ew", padx=10, pady=5)
        current_row += 1

        # Tên Tài Liệu
        Label(master, text="3. Tên Tài Liệu:", font=("Arial", 10, "bold"), bg='#f0f0f0').grid(row=current_row, column=0, sticky="w", pady=5)
        Entry(master, textvariable=self.doc_name_var, width=50, bd=2, relief="groove").grid(row=current_row, column=1, sticky="ew", padx=10, pady=5)
        current_row += 1

        # Nội Dung Tài Liệu
        Label(master, text="4. Nội Dung:", font=("Arial", 10, "bold"), bg='#f0f0f0').grid(row=current_row, column=0, sticky="nw", pady=10)
        self.content_text = Text(master, wrap=WORD, width=60, height=15, bd=2, relief="groove", font=("Arial", 10))
        self.content_text.grid(row=current_row, column=1, sticky="ew", padx=10, pady=10)
        current_row += 1
        
        # --- Thanh cuộn cho Nội Dung ---
        scrollbar = Scrollbar(master, command=self.content_text.yview)
        self.content_text['yscrollcommand'] = scrollbar.set
        scrollbar.grid(row=current_row-1, column=2, sticky='ns')

        # --- Nút Lưu Tài Liệu ---
        save_button = Button(master, text="💾 LƯU TÀI LIỆU (Tạo Thư Mục)", command=self.save_action, 
                             font=("Arial", 12, "bold"), bg="#10b981", fg="white", 
                             activebackground="#059669", activeforeground="white", 
                             pady=8, relief="raised", bd=3)
        save_button.grid(row=current_row, column=0, columnspan=2, pady=15, sticky="ew")
        current_row += 1

        # --- Khu vực hiển thị Trạng thái/Kết quả ---
        self.status_label = Label(master, text=f"Thư mục gốc: {BASE_DIR}", 
                                  font=("Arial", 9), fg="#4b5563", bg='#f0f0f0', wraplength=500, justify=LEFT)
        self.status_label.grid(row=current_row, column=0, columnspan=2, sticky="ew", pady=5)

    def save_action(self):
        """ Lấy dữ liệu từ giao diện và gọi hàm lưu trữ cục bộ. """
        subject = self.subject_var.get()
        topic = self.topic_var.get()
        doc_name = self.doc_name_var.get()
        content = self.content_text.get("1.0", END).strip()

        result_message = save_document_locally(subject, topic, doc_name, content)
        
        # Cập nhật nhãn trạng thái
        self.status_label.config(text=result_message)
        
        if "THÀNH CÔNG" in result_message:
            # Thông báo thành công và xóa nội dung (trừ Môn học/Chủ đề)
            messagebox.showinfo("Thành Công", "Đã lưu tài liệu thành công!")
            self.doc_name_var.set("")
            self.content_text.delete("1.0", END)
            self.status_label.config(fg="#047857")
        else:
            messagebox.showerror("Lỗi Lưu Trữ", result_message)
            self.status_label.config(fg="#dc2626")


if __name__ == "__main__":
    # Khởi tạo cửa sổ chính
    root = Tk()
    # Cho phép cửa sổ thay đổi kích thước theo chiều ngang
    root.grid_columnconfigure(1, weight=1) 
    
    # Chạy ứng dụng
    app = DocumentManagerApp(root)
    root.mainloop()
