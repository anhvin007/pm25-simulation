import numpy as np
import json
import os

class EmissionManager:
    def __init__(self, config_path="../data/input/sources.json", nx=100, ny=100):
        self.nx = nx
        self.ny = ny
        self.sources = self._load_config(config_path)
        self.h_std = 500.0 # Chiều cao lớp biên tiêu chuẩn (m)
        
        # Tiền tính toán Ma trận không gian Indicator W(x,y)
        self.base_emission_matrix = np.zeros((self.nx, self.ny), dtype=np.float32)
        self._build_indicator_matrix()
        
    def _load_config(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Không tìm thấy file cấu hình: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def _build_indicator_matrix(self):
        """Khởi tạo ma trận phát thải tĩnh W(x,y) cho toàn bộ không gian lưới."""
        for src in self.sources:
            x, y = src['grid_x'], src['grid_y']
            sx, sy = src['size_x'], src['size_y']
            s_base = src['s_base']
            
            # Đổ dữ liệu s_base vào vùng không gian công trường chiếm dụng
            self.base_emission_matrix[x:x+sx, y:y+sy] = s_base

    def get_activity_factor(self, hour):
        """Lấy hệ số phát thải theo lịch trình thi công."""
        if 0 <= hour < 6: return 0.05
        elif 6 <= hour < 7: return 0.30
        elif 7 <= hour < 11: return 1.00
        elif 11 <= hour < 13: return 0.40
        elif 13 <= hour < 17: return 1.00
        elif 17 <= hour < 19: return 0.30
        else: return 0.05 # 19:00 - 24:00

    def get_emission_matrix(self, dt_timestamp, current_blh):
        """
        Sinh ma trận phát thải S(x,y,t) tại một thời điểm cụ thể.
        Bao gồm hiệu ứng nén của trần khí quyển (Lid effect).
        """
        hour = dt_timestamp.hour + dt_timestamp.minute / 60.0
        factor = self.get_activity_factor(hour)
        
        # Áp dụng công thức: S(t) = S_base * factor * (H_std / BLH) * W(x,y)
        lid_effect = self.h_std / max(current_blh, 100.0) # Tránh chia cho 0
        
        return self.base_emission_matrix * factor * lid_effect

if __name__ == "__main__":
    import pandas as pd
    
    em = EmissionManager()
    test_time = pd.Timestamp('2025-06-05 09:30:00') # Đang trong ca làm việc (factor=1.0)
    test_blh = 400.0 # Thấp hơn chuẩn -> Bụi sẽ nén đặc hơn
    
    S_t = em.get_emission_matrix(test_time, test_blh)
    print(f"Tổng khối lượng phát thải tại {test_time}: {np.sum(S_t)} μg/m3/h")