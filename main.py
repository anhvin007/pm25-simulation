import subprocess
import os
import sys
import time

def run_pipeline():
    print("="*60)
    print(" KHỞI ĐỘNG HỆ THỐNG MÔ PHỎNG ĐỘNG LỰC HỌC PM2.5 ".center(60, "="))
    print("="*60)
    
    # Xác định thư mục src để set working directory, tránh lỗi sai đường dẫn tương đối
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, 'src')
    
    # Danh sách các tiến trình cần chạy theo thứ tự
    pipeline_steps = [
        ("BƯỚC 1: Sinh dữ liệu Khí tượng học", "weather_gen.py"),
        ("BƯỚC 2: Giải hệ phương trình PDE (Numba JIT)", "pde_solver.py"),
        ("BƯỚC 3: Kết xuất Đồ họa & Video Engine", "video_engine.py")
    ]
    
    total_start_time = time.time()
    
    for step_name, script_name in pipeline_steps:
        print(f"\n{step_name}")
        print(f"Executing: {script_name}...")
        
        # Chạy script bằng subprocess
        result = subprocess.run([sys.executable, script_name], cwd=src_dir)
        
        # Kiểm tra nếu có lỗi văng ra từ script con
        if result.returncode != 0:
            print(f"\n[LỖI NGIÊM TRỌNG] Tiến trình {script_name} thất bại. Dừng hệ thống!")
            sys.exit(1)
            
    total_elapsed = time.time() - total_start_time
    print("\n" + "="*60)
    print(f" LUỒNG DỮ LIỆU HOÀN TẤT THÀNH CÔNG! (Tổng thời gian: {total_elapsed:.2f}s) ".center(60, "="))
    print("="*60)
    print("\nHướng dẫn khởi động Dashboard:")
    print(" Mở terminal mới và gõ lệnh:")
    print("    cd dashboard")
    print("    streamlit run app.py\n")

if __name__ == "__main__":
    # Đảm bảo các thư mục data tồn tại trước khi chạy
    os.makedirs(os.path.join(os.path.dirname(__file__), "data", "input"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "data", "output"), exist_ok=True)
    
    run_pipeline()