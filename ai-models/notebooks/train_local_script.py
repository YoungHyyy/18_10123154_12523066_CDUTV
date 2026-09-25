import json
import time
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score, roc_curve,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

import sys
sys.path.insert(0, "/home/claude/work2")
from colmap import COLMAP

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

ROOT = Path("/home/claude/work2")
FIG_DIR = ROOT / "figures"
MODEL_DIR = ROOT / "models"
FIG_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1) LOAD DATA — cùng nguồn Breast Cancer Wisconsin (Diagnostic), đổi tên cột
#    đúng theo định dạng CSV thật trên Kaggle (radius_mean, texture_mean, ...)
# ---------------------------------------------------------------------------
raw = load_breast_cancer(as_frame=True)
df = raw.frame.copy()
df = df.rename(columns=COLMAP)
df["diagnosis"] = raw.frame["target"].map({0: "M", 1: "B"})
df["id"] = range(1, len(df) + 1)
df["Unnamed: 32"] = np.nan
df = df.drop(columns=["target"])

feature_cols = list(COLMAP.values())
df_clean = df.drop(columns=["id", "Unnamed: 32"])

n_rows, n_cols = df.shape
missing_total = int(df_clean.isnull().sum().sum())
dup_total = int(df_clean.duplicated().sum())
class_counts = df_clean["diagnosis"].value_counts()
print(f"Rows={n_rows}, Cols(raw)={n_cols}, Missing(clean)={missing_total}, Duplicates={dup_total}")
print(class_counts)

X = df_clean[feature_cols]
y = df_clean["diagnosis"]  # giữ dạng nhãn chữ M/B như notebook gốc

# ---------------------------------------------------------------------------
# 2) EDA — lưu đầy đủ tất cả hình (khác bản gốc: bản gốc chỉ show(), không lưu)
# ---------------------------------------------------------------------------
plt.figure(figsize=(7, 5))
ax = sns.countplot(data=df_clean, x="diagnosis", order=["B", "M"])
ax.set_title("Phân bố chẩn đoán khối u")
ax.set_xlabel("Diagnosis"); ax.set_ylabel("Số lượng mẫu")
for c in ax.containers: ax.bar_label(c)
plt.tight_layout(); plt.savefig(FIG_DIR / "01_target_distribution.png", dpi=150); plt.close()

features_to_plot = ["radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean", "compactness_mean"]
for feature in features_to_plot:
    plt.figure(figsize=(7, 4))
    sns.histplot(data=df_clean, x=feature, hue="diagnosis", kde=True)
    plt.title(f"Phân bố {feature} theo chẩn đoán")
    plt.tight_layout()
    plt.savefig(FIG_DIR / f"02_hist_{feature}.png", dpi=150)
    plt.close()

plt.figure(figsize=(10, 6))
sns.boxplot(data=df_clean, x="diagnosis", y="radius_mean")
plt.title("Phân bố radius_mean theo chẩn đoán")
plt.tight_layout(); plt.savefig(FIG_DIR / "03_boxplot_radius_mean.png", dpi=150); plt.close()

plt.figure(figsize=(16, 12))
corr = X.corr()
sns.heatmap(corr, cmap="coolwarm", center=0)
plt.title("Ma trận tương quan giữa các đặc trưng")
plt.tight_layout(); plt.savefig(FIG_DIR / "04_correlation_heatmap.png", dpi=150); plt.close()

plt.figure(figsize=(10, 3))
miss = df_clean[feature_cols].isnull().sum()
plt.bar(range(len(miss)), miss.values)
plt.xticks([])
plt.title(f"Số giá trị thiếu theo từng cột (tổng = {missing_total})")
plt.tight_layout(); plt.savefig(FIG_DIR / "05_missing_values.png", dpi=150); plt.close()

# ---------------------------------------------------------------------------
# 3) CHIA TRAIN/TEST + STANDARDIZATION (gộp vào Pipeline, không tách rời)
# ---------------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
split_stats = {
    "train_size": len(X_train), "test_size": len(X_test),
    "train_class_ratio": y_train.value_counts(normalize=True).to_dict(),
    "test_class_ratio": y_test.value_counts(normalize=True).to_dict(),
}
print(split_stats)

# ---------------------------------------------------------------------------
# 4) HUẤN LUYỆN 5 MODEL VỚI GridSearchCV (thay vì tham số cố định)
# ---------------------------------------------------------------------------
candidates = {
    "Logistic Regression": (
        Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=5000, random_state=42))]),
        {"clf__C": [0.01, 0.1, 1, 10]},
    ),
    "KNN": (
        Pipeline([("scaler", StandardScaler()), ("clf", KNeighborsClassifier())]),
        {"clf__n_neighbors": [3, 5, 7, 9, 11]},
    ),
    "SVM": (
        Pipeline([("scaler", StandardScaler()), ("clf", SVC(kernel="rbf", probability=True, random_state=42))]),
        {"clf__C": [0.1, 1, 10], "clf__gamma": ["scale", "auto"]},
    ),
    "Decision Tree": (
        Pipeline([("clf", DecisionTreeClassifier(random_state=42))]),
        {"clf__max_depth": [3, 5, 7, None], "clf__min_samples_leaf": [1, 5, 10]},
    ),
    "Random Forest": (
        Pipeline([("clf", RandomForestClassifier(random_state=42))]),
        {"clf__n_estimators": [100, 200], "clf__max_depth": [None, 5, 10]},
    ),
}

results = []
fitted = {}
for name, (pipe, grid) in candidates.items():
    search = GridSearchCV(pipe, grid, cv=5, scoring="f1_macro", n_jobs=-1)
    t0 = time.time()
    search.fit(X_train, y_train)
    train_time = time.time() - t0
    best = search.best_estimator_
    fitted[name] = best

    t0 = time.time()
    y_pred = best.predict(X_test)
    predict_time = (time.time() - t0) / len(X_test)
    y_proba = best.predict_proba(X_test)[:, list(best.classes_).index("M")]

    acc_train = accuracy_score(y_train, best.predict(X_train))
    acc_test = accuracy_score(y_test, y_pred)
    y_test_binary = (y_test == "M").astype(int)

    metrics = {
        "Model": name,
        "best_params": search.best_params_,
        "Accuracy_train": round(acc_train, 4),
        "Accuracy": round(acc_test, 4),
        "Precision": round(precision_score(y_test, y_pred, pos_label="M"), 4),
        "Recall": round(recall_score(y_test, y_pred, pos_label="M"), 4),
        "F1-score": round(f1_score(y_test, y_pred, pos_label="M"), 4),
        "ROC-AUC": round(roc_auc_score(y_test_binary, y_proba), 4),
        "train_time_s": round(train_time, 3),
        "predict_time_s_per_sample": round(predict_time, 5),
        "overfit_gap": round(acc_train - acc_test, 4),
    }
    results.append(metrics)
    print(metrics)

    cm = confusion_matrix(y_test, y_pred, labels=["B", "M"])
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["B", "M"], yticklabels=["B", "M"])
    plt.title(f"Confusion Matrix - {name}")
    plt.xlabel("Dự đoán"); plt.ylabel("Thực tế")
    plt.tight_layout()
    safe_name = name.replace(" ", "_").lower()
    plt.savefig(FIG_DIR / f"cm_{safe_name}.png", dpi=150)
    plt.close()

results_df = pd.DataFrame(results).sort_values("F1-score", ascending=False)
results_df.to_csv(MODEL_DIR / "metrics_comparison.csv", index=False)
print("\n=== BẢNG SO SÁNH (sắp theo F1) ===")
print(results_df[["Model", "Accuracy_train", "Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC", "overfit_gap"]])

# ROC curve tổng hợp
plt.figure(figsize=(10, 7))
for name, best in fitted.items():
    y_proba = best.predict_proba(X_test)[:, list(best.classes_).index("M")]
    y_test_binary = (y_test == "M").astype(int)
    fpr, tpr, _ = roc_curve(y_test_binary, y_proba)
    auc = roc_auc_score(y_test_binary, y_proba)
    plt.plot(fpr, tpr, linewidth=2, label=f"{name} (AUC = {auc:.4f})")
plt.plot([0, 1], [0, 1], linestyle="--", linewidth=1.5, label="Random classifier (AUC = 0.5000)")
plt.xlabel("False Positive Rate (FPR)"); plt.ylabel("True Positive Rate (TPR)")
plt.title("ROC Curve - So sánh 5 mô hình")
plt.legend(loc="lower right"); plt.grid(alpha=0.3); plt.tight_layout()
plt.savefig(FIG_DIR / "roc_curve_5_models.png", dpi=150)
plt.close()

# Biểu đồ so sánh 4 metric
metrics_to_plot = ["Accuracy", "Precision", "Recall", "F1-score"]
model_names = results_df["Model"].values
x = np.arange(len(model_names)); width = 0.2
plt.figure(figsize=(14, 7))
for i, metric in enumerate(metrics_to_plot):
    values = results_df[metric].values
    bars = plt.bar(x + (i - 1.5) * width, values, width, label=metric)
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
plt.xlabel("Mô hình"); plt.ylabel("Giá trị")
plt.title("So sánh Accuracy, Precision, Recall và F1-score của 5 mô hình")
plt.xticks(x, model_names, rotation=15); plt.ylim(0, 1.15); plt.legend(); plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "model_metrics_comparison.png", dpi=150)
plt.close()

# ---------------------------------------------------------------------------
# 5) CHỌN MODEL TỐT NHẤT & ĐÓNG GÓI (Pipeline gồm cả scaler)
# ---------------------------------------------------------------------------
# Ưu tiên: overfit_gap nhỏ (không quá lệch train/test) + F1/Recall/ROC-AUC cao
candidates_ok = results_df[results_df["overfit_gap"] < 0.05].sort_values("F1-score", ascending=False)
best_row = (candidates_ok.iloc[0] if len(candidates_ok) else results_df.iloc[0])
best_name = best_row["Model"]
best_pipe = fitted[best_name]

joblib.dump(best_pipe, MODEL_DIR / "model.joblib")

metadata = {
    "model_name": best_name,
    "best_params": best_row["best_params"],
    "metrics_test": {
        "accuracy": float(best_row["Accuracy"]),
        "precision": float(best_row["Precision"]),
        "recall": float(best_row["Recall"]),
        "f1": float(best_row["F1-score"]),
        "roc_auc": float(best_row["ROC-AUC"]),
    },
    "overfit_gap_train_minus_test_accuracy": float(best_row["overfit_gap"]),
    "dataset": "Breast Cancer Wisconsin (Diagnostic) - Kaggle uciml/breast-cancer-wisconsin-data",
    "n_features": len(feature_cols),
    "positive_class": "M (malignant)",
    "trained_at": pd.Timestamp.now().isoformat(),
}
(MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

schema = {
    "features": feature_cols,
    "target": "diagnosis (B=lành tính, M=ác tính)",
}
(MODEL_DIR / "schema.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False))

(ROOT / "run_summary.json").write_text(json.dumps({
    "dataset_stats": {"n_rows": n_rows, "missing_total": missing_total, "duplicates_total": dup_total, "class_counts": class_counts.to_dict()},
    "split_stats": split_stats,
    "results": results,
    "best_model": best_name,
}, indent=2, ensure_ascii=False))

print(f"\n>>> Model tốt nhất: {best_name}")
print(feature_cols)
