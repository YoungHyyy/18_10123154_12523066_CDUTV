"""Tiền xử lý dữ liệu - dùng chung cho notebook, huấn luyện và AI Service."""
import json
import zipfile
from pathlib import Path

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

AI_DIR = Path(__file__).resolve().parents[1]      # .../ai-models
ROOT = AI_DIR.parent                              # gốc repo
DATA_ZIP = AI_DIR / "data" / "dataset.zip"
MODELS_DIR = AI_DIR / "models"
FIGURES_DIR = ROOT / "docs" / "figures"

RANDOM_STATE = 42
LABEL_MAP = {"B": 0, "M": 1}                      # B = lành tính (0), M = ác tính (1)
CLASS_NAMES = {0: "benign", 1: "malignant"}


def load_data(zip_path=DATA_ZIP):
    """Đọc data.csv trong dataset.zip, bỏ cột không dùng, tách X và y."""
    with zipfile.ZipFile(zip_path) as z:
        df = pd.read_csv(z.open("data.csv"))
    df = df.drop(columns=["id", "Unnamed: 32"], errors="ignore").drop_duplicates()
    y = df["diagnosis"].map(LABEL_MAP)
    X = df.drop(columns="diagnosis")
    return X, y


def split(X, y, test_size=0.2):
    """Chia train/test TRƯỚC khi fit bất kỳ bộ xử lý nào (tránh data leakage)."""
    return train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE
    )


def make_preprocessor():
    """Điền thiếu bằng median rồi chuẩn hóa. Chỉ fit trên tập train (qua Pipeline)."""
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])


def build_schema(X, path=MODELS_DIR / "schema.json"):
    """Ghi schema.json: tên cột, kiểu, khoảng giá trị, nhãn. FE và BE dùng file này."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    schema = {
        "features": [
            {"name": c, "type": "float",
             "min": float(X[c].min()), "max": float(X[c].max())}
            for c in X.columns
        ],
        "target": "diagnosis",
        "labels": {"0": "benign", "1": "malignant"},
        "positive_class": "malignant",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    return schema