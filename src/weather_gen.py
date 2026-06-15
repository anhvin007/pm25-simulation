import numpy as np
import pandas as pd
from datetime import timedelta

class WeatherGenerator:
    def __init__(self, start_date='2025-06-05', days=15, dt_mins=10):
        self.start_date = pd.to_datetime(start_date)
        self.steps = int(days * 24 * 60 / dt_mins)
        self.dt_mins = dt_mins
        self.timestamps = [self.start_date + timedelta(minutes=i*dt_mins) for i in range(self.steps)]
        
    def generate_wind_direction(self):
        """Sinh hướng gió theo các Regime khối khí."""
        # Thời lượng các Regime (tính theo giờ) quy ra số bước (steps)
        regimes = [6, 8, 4, 10]
        steps_per_hour = 60 // self.dt_mins
        regime_steps = [r * steps_per_hour for r in regimes]
        
        # Góc cơ sở cho từng khối khí (Ví dụ: Đông Bắc, Đông Nam, Tây Nam, Tây Bắc)
        base_angles = [45, 135, 225, 315] 
        
        directions = np.zeros(self.steps)
        current_step = 0
        
        while current_step < self.steps:
            for length, base_angle in zip(regime_steps, base_angles):
                if current_step >= self.steps:
                    break
                
                end_step = min(current_step + length, self.steps)
                # Nhiễu động epsilon thuộc [-10, 10]
                epsilon = np.random.uniform(-10, 10, end_step - current_step)
                directions[current_step:end_step] = base_angle + epsilon
                
                current_step = end_step
                
        # Giữ góc trong khoảng [0, 360)
        return directions % 360

    def generate_wind_speed(self):
        """Sinh tốc độ gió (km/h) mức độ yếu, ưu tiên gió lặng đến nhẹ."""
        speed = np.zeros(self.steps)
        speed[0] = 3.0 # Giá trị khởi tạo: Gió nhẹ 3 km/h
        
        for i in range(1, self.steps):
            # Quá trình AR(1) được ép hệ số để gió dao động quanh mức 2 - 4 km/h
            # Công thức tính trung bình (mean): 0.5 / (1 - 0.85) = 3.33 km/h
            noise = np.random.normal(0, 0.5) # Giảm biên độ nhiễu
            speed[i] = speed[i-1] * 0.85 + 0.5 + noise
            
        # Cắt cụt nghiêm ngặt: Gió tối thiểu 0.1 km/h, tối đa chỉ 8.0 km/h
        return np.clip(speed, 0.1, 8.0)

    def generate_rain_markov(self):
        """Sinh lượng mưa (mm/h) bằng Xích Markov 2 trạng thái."""
        # Ma trận chuyển trạng thái (0: Tạnh, 1: Mưa)
        # Xác suất giữ nguyên trạng thái Tạnh rất cao (95%)
        P_00, P_01 = 0.95, 0.05
        P_10, P_11 = 0.15, 0.85
        
        rain_intensity = np.zeros(self.steps)
        current_state = 0
        
        for i in range(self.steps):
            r = np.random.rand()
            if current_state == 0:
                current_state = 1 if r > P_00 else 0
            else:
                current_state = 0 if r > P_11 else 1
                
            if current_state == 1:
                # Nếu mưa, lấy mẫu cường độ từ phân phối mũ (để ưu tiên mưa nhỏ, hiếm mưa to)
                intensity = np.random.exponential(scale=5.0)
                rain_intensity[i] = np.clip(intensity, 0.1, 50.0)
                
        return rain_intensity

    def generate_diurnal_cycles(self):
        """Sinh BLH (m), Nhiệt độ (°C) và Độ che phủ mây (%) dựa trên chu kỳ ngày đêm."""
        hours = np.array([ts.hour + ts.minute/60 for ts in self.timestamps])
        
        # 1. Chiều cao lớp biên (BLH): Cao nhất vào giữa trưa (~1500m), thấp nhất vào ban đêm (~300m)
        # Sử dụng hàm -cosine lùi pha để đỉnh điểm rơi vào 14:00 (14h)
        blh_base = 900 - 600 * np.cos((hours - 2) * np.pi / 12)
        blh_noise = np.random.normal(0, 50, self.steps)
        blh = np.clip(blh_base + blh_noise, 200, 2000)
        
        # 2. Nhiệt độ: Dao động từ 25°C đêm đến 35°C ngày
        temp_base = 30 - 5 * np.cos((hours - 3) * np.pi / 12)
        temp_noise = np.random.normal(0, 0.5, self.steps)
        temperature = np.clip(temp_base + temp_noise, 20, 40)
        
        # 3. Mây (%): Mạch đập ngẫu nhiên, thiên về nhiều mây vào chiều tối
        cloud_cover = np.clip(np.random.normal(50, 20, self.steps) + 20 * np.sin(hours * np.pi / 12), 0, 100)
        
        return blh, temperature, cloud_cover

    def calculate_pg_stability(self, speed_kmh, cloud_cover, hours):
        """Tính cấp độ ổn định Pasquill-Gifford."""
        speed_ms = speed_kmh / 3.6
        pg_classes = []
        
        for v, cc, h in zip(speed_ms, cloud_cover, hours):
            is_day = 6 <= h < 18
            
            if is_day:
                if cc < 50:
                    pg = 'A' if v <= 2.0 else ('B' if v <= 5.0 else 'C')
                else:
                    pg = 'B' if v <= 2.0 else ('C' if v <= 5.0 else 'D')
            else:
                if cc >= 50:
                    pg = 'E' if v <= 2.0 else 'D'
                else:
                    pg = 'F' if v <= 2.0 else ('E' if v <= 5.0 else 'D')
            
            pg_classes.append(pg)
            
        return pg_classes

    def generate(self, output_path=None):
        """Tổng hợp dữ liệu và xuất ra DataFrame."""
        print("Đang sinh dữ liệu khí tượng...")
        
        wind_dir = self.generate_wind_direction()
        wind_speed = self.generate_wind_speed()
        rainfall = self.generate_rain_markov()
        blh, temperature, cloud_cover = self.generate_diurnal_cycles()
        hours = [ts.hour for ts in self.timestamps]
        
        pg_stability = self.calculate_pg_stability(wind_speed, cloud_cover, hours)
        
        df = pd.DataFrame({
            'timestamp': self.timestamps,
            'temperature': np.round(temperature, 2),
            'wind_speed': np.round(wind_speed, 2),
            'wind_direction': np.round(wind_dir, 2),
            'cloud_cover': np.round(cloud_cover, 2),
            'rainfall': np.round(rainfall, 2),
            'blh': np.round(blh, 2),
            'pg_stability': pg_stability
        })
        
        df.set_index('timestamp', inplace=True)
        
        if output_path:
            # Lưu định dạng parquet để tối ưu dung lượng và tốc độ đọc
            df.to_parquet(output_path)
            print(f"Đã lưu dữ liệu tại: {output_path}")
            
        return df

if __name__ == "__main__":
    import os
    
    # Đảm bảo thư mục output tồn tại
    os.makedirs("../data/output", exist_ok=True)
    
    # Khởi tạo và chạy test
    wg = WeatherGenerator(start_date='2025-06-05', days=15, dt_mins=10)
    df_weather = wg.generate(output_path="../data/output/meteorology.parquet")
    
    print("\nTrích xuất 5 dòng dữ liệu đầu tiên:")
    print(df_weather.head())