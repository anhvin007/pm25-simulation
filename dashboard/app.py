import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# Cấu hình trang
st.set_page_config(page_title="PM2.5 Dynamics Dashboard", layout="wide", page_icon="🌬️")

# --- HÀM NẠP DỮ LIỆU ĐỂ CACHE ---
@st.cache_data
def load_data():
    weather_df = pd.read_parquet("../data/output/meteorology.parquet")
    cube = np.load("../data/output/PM25_Cube.npy")
    return weather_df, cube

# Khởi chạy nạp dữ liệu
try:
    df_weather, pm25_cube = load_data()
    total_steps, nx, ny = pm25_cube.shape
except Exception as e:
    st.error("Chưa tìm thấy dữ liệu mô phỏng. Vui lòng chạy các module src/ trước.")
    st.stop()

# --- HEADER TỔNG QUAN ---
st.title("🌬️ Hệ thống Phân tích Động lực học PM2.5")
st.markdown("Mô phỏng sự phát tán bụi mịn từ công trường xây dựng dưới tác động của khí tượng học.")

# Tạo 4 Tab theo đúng thiết kế
tab2, tab3, tab4 = st.tabs([ "🏔️ 3D PM2.5 Surface", "📈 Station History", "🌤️ Meteorology"])


# --- TAB 2: ĐỊA HÌNH 3D PM2.5 ---
with tab2:
    st.header("Bản đồ Địa hình Nồng độ 3D")
    
    # Thanh trượt chọn thời điểm
    step_idx = st.slider("Chọn mốc thời gian (bước):", 0, total_steps - 1, 100)
    selected_time = df_weather.index[step_idx]
    st.subheader(f"Thời gian: {selected_time.strftime('%Y-%m-%d %H:%M')}")
    
    # Lấy ma trận tại thời điểm t
    Z = pm25_cube[step_idx]
    
    # Vẽ Surface Plot bằng Plotly
    fig_3d = go.Figure(data=[go.Surface(z=Z, colorscale='Hot', cmin=0, cmax=250)])
    fig_3d.update_layout(
        title='Phân bố Không gian PM2.5',
        autosize=True, width=1500, height=1000,
        scene=dict(
            xaxis_title='Trục X (Đông - Tây)',
            yaxis_title='Trục Y (Bắc - Nam)',
            zaxis_title='Nồng độ PM2.5 (μg/m³)'
        )
    )
    st.plotly_chart(fig_3d, use_container_width=True)

# --- TAB 3: LỊCH SỬ TRẠM ĐO ---
with tab3:
    st.header("Lịch sử Ô nhiễm tại Trạm Trung tâm")
    st.markdown("Chuỗi thời gian trích xuất từ tọa độ ô lưới (50, 50).")
    
    # Trích xuất dữ liệu chuỗi tại điểm trung tâm
    station_history = pm25_cube[:, 50, 50]
    
    fig_history = px.line(x=df_weather.index, y=station_history, 
                          labels={'x': 'Thời gian', 'y': 'Nồng độ PM2.5 (μg/m³)'},
                          title="Biến thiên nồng độ PM2.5 (Trạm Tâm lưới)")
    fig_history.update_traces(line_color='red')
    st.plotly_chart(fig_history, use_container_width=True)

# --- TAB 4: BIẾN KHÍ TƯỢNG ---
with tab4:
    st.header("Dữ liệu Khí tượng Đầu vào")
    
    col1, col2 = st.columns(2)
    with col1:
        fig_ws = px.line(df_weather, y='wind_speed', title='Tốc độ gió (km/h)')
        st.plotly_chart(fig_ws, use_container_width=True)
        
        fig_temp = px.line(df_weather, y='temperature', title='Nhiệt độ (°C)')
        fig_temp.update_traces(line_color='orange')
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with col2:
        fig_rain = px.line(df_weather, y='rainfall', title='Lượng mưa (mm/h)')
        fig_rain.update_traces(line_color='blue')
        st.plotly_chart(fig_rain, use_container_width=True)
        
        fig_blh = px.line(df_weather, y='blh', title='Chiều cao Lớp biên - BLH (m)')
        fig_blh.update_traces(line_color='purple')
        st.plotly_chart(fig_blh, use_container_width=True)