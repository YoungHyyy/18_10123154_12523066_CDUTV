# Dataset

- Tên: Breast Cancer Wisconsin (Diagnostic) Data Set
- Nguồn: UCI / Kaggle (`uciml/breast-cancer-wisconsin-data`) — trong bản chạy này lấy qua
  `sklearn.datasets.load_breast_cancer()` (cùng dữ liệu gốc, 569 mẫu / 30 đặc trưng, không cần tải file ngoài).
- Cột mục tiêu: `diagnosis` — `M` = Malignant (ác tính, mã hoá 1), `B` = Benign (lành tính, mã hoá 0)
- Thống kê: 569 dòng, 30 đặc trưng số, 0 giá trị thiếu, 0 dòng trùng lặp.
- Phân bố nhãn: B = 357 (62.7%), M = 212 (37.3%) — hơi mất cân bằng nhẹ, đã dùng `stratify=y` khi chia train/test.

Nếu nhóm muốn nộp bản CSV thật từ Kaggle để đúng quy trình "tải dataset" trong yêu cầu:
1. `pip install kaggle`, đặt `kaggle.json` (KHÔNG commit).
2. `kaggle datasets download -d uciml/breast-cancer-wisconsin-data -p ai-models/data --unzip`
3. Sửa `train.py` phần LOAD DATA để đọc `data.csv` thay vì `load_breast_cancer()`, bỏ cột `id`/`Unnamed: 32`.
