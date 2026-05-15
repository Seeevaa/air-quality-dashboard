# Dashboard Kualitas Udara Beijing (2013–2017)

## Deskripsi
Dashboard interaktif untuk menganalisis kualitas udara di 12 stasiun 
pemantauan Beijing periode 2013–2017 menggunakan dataset PRSA.

## Setup Environment

```bash
conda create -n air-quality python=3.10
conda activate air-quality
pip install -r requirements.txt
```

## Menjalankan Dashboard

```bash
streamlit run dashboard/dashboard.py
```

## Struktur Direktori

```
submission/
├── dashboard/
│   ├── main_data.csv
│   └── dashboard.py
├── data/
│   └── (12 file CSV PRSA)
├── notebook.ipynb
├── README.md
└── requirements.txt
```