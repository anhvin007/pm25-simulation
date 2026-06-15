import cv2
import numpy as np
import pandas as pd
import os

class VideoEngine:
    def __init__(self, cube_path="../data/output/PM25_Cube.npy", weather_path="./data/output/meteorology.parquet"):
        print("Đang nạp dữ liệu không gian 3D...")
        self.cube = np.load(cube_path)
        self.df_weather = pd.read_parquet(weather_path)
        
        self.total_steps, self.nx, self.ny = self.cube.shape
        self.width, self.height = 800, 800
        
        self.fps = 15
        self.out_path = "../data/output/simulation_raw.mp4"
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.out_path, self.fourcc, self.fps, (self.width, self.height))
        
        # 1. NỀN TRẮNG
        self.base_map = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
        
        # Đồng bộ tọa độ (Lưới 100x100 -> Ảnh 800x800, tỷ lệ 1:8)
        # Công trường A (Grid: X=40, Y=30 -> Pixel: 320, 240)
        cv2.rectangle(self.base_map, (320, 240), (336, 256), (0, 0, 0), 2)
        cv2.putText(self.base_map, "CT A", (280, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Công trường B (Grid: X=40, Y=70 -> Pixel: 320, 560)
        cv2.rectangle(self.base_map, (320, 560), (336, 576), (0, 0, 0), 2)
        cv2.putText(self.base_map, "CT B", (280, 570), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Trạm đo (Grid: 50, 50 -> Pixel: 400, 400)
        cv2.circle(self.base_map, (400, 400), 8, (100, 100, 100), -1) 
        cv2.putText(self.base_map, "Station", (415, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

    def apply_heatmap_effect(self, C_matrix):
        """Tạo bản đồ Heatmap truyền thống (JET colormap)."""
        C_matrix = np.nan_to_num(C_matrix, nan=0.0, posinf=150.0, neginf=0.0)
        C_resized = cv2.resize(C_matrix, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        C_norm = np.clip(C_resized / 150.0 * 255.0, 0, 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(C_norm, cv2.COLORMAP_JET)
        mask = (C_resized > 2.0).astype(np.uint8)[:, :, np.newaxis]
        return heatmap, mask

    def get_time_of_day_label(self, hour):
        """Phân loại thời gian trong ngày."""
        if 5 <= hour < 11: return "SANG"
        elif 11 <= hour < 13: return "TRUA"
        elif 13 <= hour < 18: return "CHIEU"
        elif 18 <= hour < 22: return "TOI"
        else: return "DEM KHUYA"

    def draw_rain_effect(self, frame, rain_intensity):
        """Vẽ hiệu ứng mưa rơi lên frame."""
        if rain_intensity <= 0.1:
            return frame
            
        # Phân loại lượng mưa (mm/h)
        if rain_intensity <= 2.5: rain_level, num_drops = "Rat nho", 20
        elif rain_intensity <= 10.0: rain_level, num_drops = "Nho", 50
        elif rain_intensity <= 20.0: rain_level, num_drops = "Vua", 100
        elif rain_intensity <= 50.0: rain_level, num_drops = "Lon", 200
        else: rain_level, num_drops = "Rat lon", 400
        
        # Vẽ các vệt mưa ngẫu nhiên
        for _ in range(num_drops):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            length = np.random.randint(10, 30)
            cv2.line(frame, (x, y), (x - 2, y + length), (255, 150, 100), 1) # Màu xanh nhạt
            
        cv2.putText(frame, f"Mua: {rain_level}", (400, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 100, 50), 2)
        return frame

    def draw_hud(self, frame, timestamp, row):
        """Vẽ lớp thông tin đồ họa (HUD)."""
        # Màu chữ (Đen do nền trắng)
        text_color = (0, 0, 0)
        
        # 1. Thời gian & Phân loại buổi
        hour = timestamp.hour + timestamp.minute / 60.0
        time_label = self.get_time_of_day_label(hour)
        time_str = timestamp.strftime('%Y-%m-%d %H:%M')
        cv2.putText(frame, f"{time_str} ({time_label})", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, text_color, 2)
        
        # 2. Thanh biểu đồ BLH (Chiều cao lớp biên)
        # Giả sử BLH max = 2000m
        blh_val = int(np.clip(row['blh'], 0, 2000))
        bar_height_blh = int((blh_val / 2000.0) * 300)
        cv2.rectangle(frame, (720, 650 - bar_height_blh), (750, 650), (128, 0, 128), -1) # Màu tím
        cv2.rectangle(frame, (720, 350), (750, 650), text_color, 2) # Viền cột
        cv2.putText(frame, "BLH", (715, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)
        cv2.putText(frame, f"{blh_val}m", (710, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)

        # 3. Thanh biểu đồ Sức gió
        # Giả sử Wind max = 30 km/h
        wind_val = np.clip(row['wind_speed'], 0, 30)
        bar_height_wind = int((wind_val / 30.0) * 300)
        cv2.rectangle(frame, (660, 650 - bar_height_wind), (690, 650), (0, 200, 255), -1) # Màu vàng cam
        cv2.rectangle(frame, (660, 350), (690, 650), text_color, 2) # Viền cột
        cv2.putText(frame, "WIND", (650, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)
        cv2.putText(frame, f"{wind_val:.1f}", (650, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
        
        # Hướng gió (Vẽ text góc trên trái)
        cv2.putText(frame, f"Wind Dir: {row['wind_direction']:.0f} deg", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 1)
        
        return frame

    def render(self):
        print(f"Bắt đầu kết xuất Video {self.total_steps} frames...")
        
        for step in range(self.total_steps):
            timestamp = self.df_weather.index[step]
            row = self.df_weather.iloc[step]
            C_t = self.cube[step]
            
            # Lấy layer heatmap
            heatmap_layer, mask = self.apply_heatmap_effect(C_t)
            
            # Trộn 60% heatmap + 40% nền trắng
            frame = np.where(mask > 0, cv2.addWeighted(heatmap_layer, 0.6, self.base_map, 0.4, 0), self.base_map)
            
            # Vẽ hiệu ứng mưa (Lớp 1)
            frame = self.draw_rain_effect(frame, row['rainfall'])
            
            # Vẽ HUD (Lớp 2)
            frame = self.draw_hud(frame, timestamp, row)
            
            self.writer.write(frame)
            
            if (step + 1) % 500 == 0:
                print(f"Đã render: {step + 1}/{self.total_steps} frames")
                
        self.writer.release()
        print("Render hoàn tất! Đang convert chuẩn MP4 (h264)...")
        final_mp4 = "../data/output/output_simulation.mp4"
        os.system(f"ffmpeg -y -i {self.out_path} -vcodec libx264 {final_mp4}")
        if os.path.exists(final_mp4) and os.path.exists(self.out_path):
            os.remove(self.out_path)

if __name__ == "__main__":
    engine = VideoEngine()
    engine.render()