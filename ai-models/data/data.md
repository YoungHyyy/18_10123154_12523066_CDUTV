# Dữ liệu Breast Cancer Wisconsin (Diagnostic)

## 1. Nguồn và giấy phép

- Tên dataset: **Breast Cancer Wisconsin (Diagnostic) Data Set**.
- Nguồn tải: [Kaggle - uciml/breast-cancer-wisconsin-data](https://www.kaggle.com/datasets/uciml/breast-cancer-wisconsin-data).
- Nguồn gốc: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic).
- Giấy phép trên Kaggle: **CC BY-NC-SA 4.0** ([Creative Commons](https://creativecommons.org/licenses/by-nc-sa/4.0/)).
- Mục đích sử dụng trong project: học tập và minh họa quy trình machine learning; không dùng để chẩn đoán y khoa thực tế.

## 2. Artifact trong repository

- File: `ai-models/data/dataset.zip`.
- Kích thước archive hiện tại: khoảng 49 KB.
- File bên trong archive: `data.csv`.
- Notebook và `ai-models/src/preprocess.py` đọc file này trực tiếp, không phụ thuộc đường dẫn `/content` hay một repository bên ngoài.

Đọc dữ liệu bằng Python:

```python
import zipfile
import pandas as pd

with zipfile.ZipFile("ai-models/data/dataset.zip") as archive:
	df = pd.read_csv(archive.open("data.csv"))
```

## 3. Quy mô và chất lượng dữ liệu

| Thuộc tính                       | Giá trị |
| -------------------------------- | ------: |
| Số mẫu                           |     569 |
| Số cột gốc                       |      33 |
| Số đặc trưng dùng cho model      |      30 |
| Lớp lành tính `B`                |     357 |
| Lớp ác tính `M`                  |     212 |
| Dòng trùng lặp                   |       0 |
| Ô thiếu trong dữ liệu gốc        |     569 |
| Ô thiếu sau khi bỏ `Unnamed: 32` |       0 |

569 ô thiếu trong dữ liệu gốc đều thuộc cột `Unnamed: 32`, đây là cột rỗng sinh ra từ file CSV. Cột này được loại bỏ trước khi tách feature và target.

## 4. Các cột dữ liệu

- `id`: mã định danh mẫu, không dùng làm feature vì không mang ý nghĩa đo lường.
- `diagnosis`: target của bài toán; `B` là benign/lành tính, `M` là malignant/ác tính.
- `Unnamed: 32`: cột rỗng, được loại bỏ.

30 feature số được tạo từ 10 phép đo đặc trưng nhân tế bào:

| Nhóm phép đo      | Các feature                                                                 |
| ----------------- | --------------------------------------------------------------------------- |
| Bán kính          | `radius_mean`, `radius_se`, `radius_worst`                                  |
| Texture           | `texture_mean`, `texture_se`, `texture_worst`                               |
| Chu vi            | `perimeter_mean`, `perimeter_se`, `perimeter_worst`                         |
| Diện tích         | `area_mean`, `area_se`, `area_worst`                                        |
| Độ mịn            | `smoothness_mean`, `smoothness_se`, `smoothness_worst`                      |
| Độ gọn            | `compactness_mean`, `compactness_se`, `compactness_worst`                   |
| Độ lõm            | `concavity_mean`, `concavity_se`, `concavity_worst`                         |
| Điểm lõm          | `concave points_mean`, `concave points_se`, `concave points_worst`          |
| Đối xứng          | `symmetry_mean`, `symmetry_se`, `symmetry_worst`                            |
| Fractal dimension | `fractal_dimension_mean`, `fractal_dimension_se`, `fractal_dimension_worst` |

Với mỗi phép đo, hậu tố có ý nghĩa:

- `_mean`: giá trị trung bình.
- `_se`: sai số chuẩn.
- `_worst`: trung bình của ba giá trị lớn nhất.

## 5. Tiền xử lý được sử dụng

Quy trình thống nhất trong `ai-models/src/preprocess.py`:

1. Đọc `data.csv` từ `dataset.zip`.
2. Loại bỏ `id` và `Unnamed: 32`.
3. Loại bỏ dòng trùng lặp.
4. Ánh xạ target: `B -> 0`, `M -> 1`.
5. Chia train/test với `stratify=y`, `test_size=0.2`, `random_state=42`.
6. Đặt `SimpleImputer(strategy="median")` và `StandardScaler` trong pipeline.

Imputer và scaler chỉ được fit bên trong pipeline trên tập train khi huấn luyện, nhằm tránh data leakage. Schema dùng chung cho model, Backend và Frontend nằm tại `ai-models/models/schema.json`.

## 6. Hạn chế và lưu ý

- Dataset là dữ liệu đo từ ảnh chọc hút kim nhỏ (FNA), không đại diện cho mọi nhóm bệnh nhân hoặc mọi quy trình lâm sàng.
- Nhãn và xác suất model chỉ phục vụ bài tập machine learning, không thay thế bác sĩ hay xét nghiệm chuyên môn.
- Khi dùng lại dataset, cần giữ attribution và điều kiện phi thương mại/chia sẻ tương tự theo CC BY-NC-SA 4.0.
