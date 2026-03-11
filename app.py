import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Weekly Habit Tracker", layout="wide")

# --- 1. Fungsi Database (CSV) ---
CSV_FILE = 'habit_data.csv'

def load_data_from_csv():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=['Tanggal', 'Habit', 'Kategori', 'Status'])

def save_data_to_csv(habit_list, db_check):
    rows = []
    # Loop melalui semua data centang yang ada di memori
    for d_key, habits in db_check.items():
        for h_name, status in habits.items():
            # Cari kategori untuk habit tersebut
            kategori = next((h['Kategori'] for h in habit_list if h['Habit'] == h_name), "Lainnya")
            rows.append({
                'Tanggal': d_key,
                'Habit': h_name,
                'Kategori': kategori,
                'Status': status
            })
    df_save = pd.DataFrame(rows)
    df_save.to_csv(CSV_FILE, index=False)

# --- 2. Inisialisasi State & Load Data ---
if 'db_check' not in st.session_state:
    df_loaded = load_data_from_csv()
    # Ubah format DataFrame CSV kembali ke Dictionary Session State
    st.session_state.db_check = {}
    for _, row in df_loaded.iterrows():
        d_key = row['Tanggal']
        h_name = row['Habit']
        if d_key not in st.session_state.db_check:
            st.session_state.db_check[d_key] = {}
        st.session_state.db_check[d_key][h_name] = bool(row['Status'])

if 'habit_list' not in st.session_state:
    # Mengambil daftar habit unik dari CSV jika ada
    df_loaded = load_data_from_csv()
    if not df_loaded.empty:
        unique_habits = df_loaded[['Habit', 'Kategori']].drop_duplicates().to_dict('records')
        st.session_state.habit_list = unique_habits
    else:
        st.session_state.habit_list = [
            {"Habit": "Workout", "Kategori": "Kesehatan"},
            {"Habit": "Baca Buku", "Kategori": "Edukasi"}
        ]

if 'categories' not in st.session_state:
    existing_cats = list(set([h['Kategori'] for h in st.session_state.habit_list]))
    st.session_state.categories = existing_cats if existing_cats else ["Kesehatan", "Edukasi", "Mental", "Kerja"]

if 'current_start_date' not in st.session_state:
    today = datetime.now()
    st.session_state.current_start_date = today - timedelta(days=today.weekday())

# --- 3. Sidebar: Kelola Habit & Kategori ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    with st.expander("📁 Kelola Kategori"):
        new_cat = st.text_input("Nama Kategori Baru")
        if st.button("➕ Tambah Kategori"):
            if new_cat and new_cat not in st.session_state.categories:
                st.session_state.categories.append(new_cat)
                st.rerun()
        
        cat_to_del = st.selectbox("Hapus Kategori", st.session_state.categories)
        if st.button("🗑️ Hapus Kategori"):
            st.session_state.categories.remove(cat_to_del)
            st.session_state.habit_list = [h for h in st.session_state.habit_list if h['Kategori'] != cat_to_del]
            save_data_to_csv(st.session_state.habit_list, st.session_state.db_check)
            st.rerun()

    with st.expander("➕ Kelola Habit"):
        new_h = st.text_input("Nama Habit Baru")
        new_c = st.selectbox("Pilih Kategori", st.session_state.categories)
        if st.button("💾 Simpan Habit"):
            if new_h:
                st.session_state.habit_list.append({"Habit": new_h, "Kategori": new_c})
                save_data_to_csv(st.session_state.habit_list, st.session_state.db_check)
                st.rerun()
        
        habit_names = [h['Habit'] for h in st.session_state.habit_list]
        h_to_del = st.selectbox("Hapus Habit", habit_names if habit_names else ["Kosong"])
        if st.button("🗑️ Hapus Habit") and habit_names:
            st.session_state.habit_list = [h for h in st.session_state.habit_list if h['Habit'] != h_to_del]
            save_data_to_csv(st.session_state.habit_list, st.session_state.db_check)
            st.rerun()

# --- 4. Navigasi Tanggal ---
st.title("📅 Pro Weekly Tracker")
c1, c2, c3 = st.columns([1,1,1])
with c1: 
    if st.button("⬅️ Minggu Lalu", use_container_width=True):
        st.session_state.current_start_date -= timedelta(days=7)
with c2:
    if st.button("🏠 Minggu Ini", use_container_width=True):
        t = datetime.now()
        st.session_state.current_start_date = t - timedelta(days=t.weekday())
with c3:
    if st.button("Minggu Depan ➡️", use_container_width=True):
        st.session_state.current_start_date += timedelta(days=7)

start_date = st.session_state.current_start_date
dates = [(start_date + timedelta(days=i)) for i in range(7)]
date_labels = [d.strftime("%a %d") for d in dates]
full_dates = [d.strftime("%Y-%m-%d") for d in dates]

st.info(f"**Periode:** {dates[0].strftime('%d %b')} - {dates[-1].strftime('%d %b %Y')}")

# --- 5. Tampilan Utama dengan TABS ---
active_categories = sorted(list(set([h['Kategori'] for h in st.session_state.habit_list])))

if not active_categories:
    st.warning("Tambahkan habit di sidebar.")
else:
    tabs = st.tabs(active_categories)
    for i, cat in enumerate(active_categories):
        with tabs[i]:
            cat_habits = [h['Habit'] for h in st.session_state.habit_list if h['Kategori'] == cat]
            df_display = pd.DataFrame(index=cat_habits, columns=date_labels)
            
            for h in cat_habits:
                for j, d_key in enumerate(full_dates):
                    df_display.loc[h, date_labels[j]] = st.session_state.db_check.get(d_key, {}).get(h, False)

            edited_df = st.data_editor(
                df_display,
                column_config={l: st.column_config.CheckboxColumn(l, width="small") for l in date_labels},
                use_container_width=True,
                key=f"editor_{cat}_{start_date.strftime('%Y%m%d')}"
            )

            # Deteksi perubahan dan simpan ke CSV
            for h in cat_habits:
                for j, d_key in enumerate(full_dates):
                    if d_key not in st.session_state.db_check: st.session_state.db_check[d_key] = {}
                    st.session_state.db_check[d_key][h] = edited_df.loc[h, date_labels[j]]

# --- 6. Tombol Simpan Manual & Download ---
st.divider()
col_save, col_dl = st.columns(2)
with col_save:
    if st.button("💾 Simpan Perubahan ke File", type="primary", use_container_width=True):
        save_data_to_csv(st.session_state.habit_list, st.session_state.db_check)
        st.success("Data tersimpan di habit_data.csv")

with col_dl:
    # Memungkinkan user mengunduh file CSV secara langsung
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'rb') as f:
            st.download_button(
                label="📥 Download File CSV (untuk Excel)",
                data=f,
                file_name=f"habit_tracker_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
