# Hệ thống Mô phỏng Động lực học Không gian - Thời gian PM2.5

Dự án này xây dựng một mô hình toán học dựa trên **Phương trình Đạo hàm riêng Đối lưu - Khuếch tán (Advection-Diffusion PDE)** để mô phỏng sự lan truyền của bụi mịn PM2.5 trong môi trường đô thị dưới tác động của khí tượng học.

## Tính năng cốt lõi
* **Mô hình Hóa Khí quyển:** Tự động sinh dữ liệu thời tiết (Gió, Mưa, BLH, Độ ổn định Pasquill-Gifford) bằng các mô hình ngẫu nhiên (AR(1), Markov Chain).
* **PDE Solver (Core Engine):** Giải phương trình vi phân bằng sơ đồ **Forward Euler** và **Upwind/Central Difference**, được tối ưu hóa hiệu năng cực hạn bằng `Numba` (JIT Compilation) cho phép tính toán trên lưới không gian 10,000 ô.
* **Video Engine:** Áp dụng kỹ thuật xử lý ảnh OpenCV để tạo bản đồ nhiệt (Heatmap) và kết xuất trực quan mô phỏng Động lực học Chất lưu (CFD) chồng lên bản đồ vệ tinh thực tế.
* **Streamlit Dashboard:** Cung cấp giao diện Web tương tác để quan sát đồ thị 3D Surface, lịch sử trạm đo và video phân tán khói bụi.

## Cấu trúc Thư mục
\`\`\`text
pm25-simulation/
├── data/
│   ├── input/               # Chứa sources.json, map_background.jpg
│   └── output/              # Chứa kết quả: PM25_Cube.npy, meteorology.parquet...
├── src/
│   ├── weather_gen.py       # Thuật toán sinh khí tượng
│   ├── emission.py          # Thuật toán phát thải
│   ├── pde_solver.py        # Động cơ giải phương trình PDE
│   └── video_engine.py      # OpenCV Renderer
├── dashboard/
│   └── app.py               # Giao diện người dùng
├── main.py                  # Script điều phối toàn bộ hệ thống
└── requirements.txt         # Danh sách thư viện
\`\`\`

## Hướng dẫn Cài đặt & Sử dụng

**1. Cài đặt môi trường:**
Yêu cầu Python 3.9+ và hệ thống đã được cài đặt FFmpeg.
\`\`\`bash
pip install -r requirements.txt
\`\`\`

**2. Khởi chạy luồng Mô phỏng:**
Chạy file điều phối chính để sinh dữ liệu, giải phương trình và render video:
\`\`\`bash
python main.py
\`\`\`

**3. Khởi động Dashboard:**
Sau khi luồng xử lý ở bước 2 hoàn tất, khởi chạy giao diện Web:
\`\`\`bash
cd dashboard
streamlit run app.py
\`\`\`
Trình duyệt sẽ tự động mở tại địa chỉ `http://localhost:8501`.