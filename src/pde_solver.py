import numpy as np
import pandas as pd
from numba import njit
import time
from emission import EmissionManager

@njit
def step_pde_numba(C, u, v, D, S, lambda_rain, dx, dy, dt):
    Nx, Ny = C.shape
    C_new = np.copy(C)
    
    for i in range(1, Nx-1):
        for j in range(1, Ny-1):
            # UPWIND SCHEME
            if u > 0:
                dC_dx = (C[i, j] - C[i-1, j]) / dx
            else:
                dC_dx = (C[i+1, j] - C[i, j]) / dx
                
            if v > 0:
                dC_dy = (C[i, j] - C[i, j-1]) / dy
            else:
                dC_dy = (C[i, j+1] - C[i, j]) / dy
                
            # CENTRAL DIFFERENCE
            d2C_dx2 = (C[i+1, j] - 2*C[i, j] + C[i-1, j]) / (dx*dx)
            d2C_dy2 = (C[i, j+1] - 2*C[i, j] + C[i, j-1]) / (dy*dy)
            
            # UPDATE
            C_new[i, j] = C[i, j] + dt * (-u*dC_dx - v*dC_dy + D*(d2C_dx2 + d2C_dy2) + S[i, j] - lambda_rain*C[i, j])
            
            if C_new[i, j] < 0:
                C_new[i, j] = 0
                
    # NEUMANN BOUNDARY
    for i in range(Nx):
        C_new[i, 0] = C_new[i, 1]
        C_new[i, Ny-1] = C_new[i, Ny-2]
    for j in range(Ny):
        C_new[0, j] = C_new[1, j]
        C_new[Nx-1, j] = C_new[Nx-2, j]
        
    C_new[0, 0] = C_new[1, 1]
    C_new[Nx-1, 0] = C_new[Nx-2, 1]
    C_new[0, Ny-1] = C_new[1, Ny-2]
    C_new[Nx-1, Ny-1] = C_new[Nx-2, Ny-2]

    return C_new

class PDESolver:
    def __init__(self, weather_data_path="../data/output/meteorology.parquet"):
        self.df_weather = pd.read_parquet(weather_data_path)
        self.emission_mgr = EmissionManager()
        self.Nx, self.Ny = 100, 100
        self.dx, self.dy = 50.0, 50.0
        self.dt_mins = 10
        self.total_steps = len(self.df_weather)
        self.cube = np.zeros((self.total_steps, self.Nx, self.Ny), dtype=np.float32)
        self.alpha, self.beta = 3.0e-2, 0.79
        self.D_dict = {'A': 180000.0, 'B': 108000.0, 'C': 72000.0, 'D': 36000.0, 'E': 18000.0, 'F': 7200.0}

    def solve(self, output_cube_path="../data/output/PM25_Cube.npy"):
        print(f"Bắt đầu giải PDE cho {self.total_steps} bước thời gian...")
        start_time = time.time()
        C_current = np.zeros((self.Nx, self.Ny), dtype=np.float32)
        
        # Tăng sub_steps lên 200 để dt <= 3s (Tuyệt đối tuân thủ điều kiện CFL)
        sub_steps = 200 
        dt_sub_hours = (self.dt_mins / 60.0) / sub_steps 
        
        for step in range(self.total_steps):
            row = self.df_weather.iloc[step]
            timestamp = self.df_weather.index[step]
            
            ws_kmh = row['wind_speed']
            wind_dir = row['wind_direction']
            blh = row['blh']
            rain = row['rainfall']
            pg_class = row['pg_stability']
            
            u = -(ws_kmh * 1000.0) * np.sin(np.radians(wind_dir))
            v = -(ws_kmh * 1000.0) * np.cos(np.radians(wind_dir))
            
            D = self.D_dict.get(pg_class, 36000.0)
            lambda_rain = self.alpha * (rain ** self.beta)
            
            # Nhân hệ số 3000 để mô phỏng một công trường quy mô cực lớn (bụi dễ quan sát)
            S_matrix = self.emission_mgr.get_emission_matrix(timestamp, blh) * 3000.0
            
            for _ in range(sub_steps):
                C_current = step_pde_numba(C_current, u, v, D, S_matrix, lambda_rain, 
                                           self.dx, self.dy, dt_sub_hours)
            
            self.cube[step] = C_current
            
            if (step + 1) % 100 == 0:
                print(f"Đã giải quyết: {step + 1}/{self.total_steps} steps...")
                
        np.save(output_cube_path, self.cube)
        elapsed = time.time() - start_time
        print(f"Hoàn tất giải PDE! Thời gian chạy: {elapsed:.2f} giây.")

if __name__ == "__main__":
    solver = PDESolver()
    solver.solve()