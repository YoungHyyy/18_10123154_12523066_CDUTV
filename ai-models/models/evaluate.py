"""Vẽ biểu đồ so sánh và phân tích lỗi."""
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay

from preprocess import FIGURES_DIR

LABELS = ["Lành tính", "Ác tính"]


def _save(name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / name, dpi=150, bbox_inches="tight")


def plot_metric_comparison(results):
    cols = ["test_recall", "test_precision", "test_f1", "test_roc_auc"]
    ax = results.set_index("model")[cols].plot.bar(figsize=(11, 5), rot=15)
    ax.set_ylim(0, 1.05); ax.set_title("So sánh metric trên tập test")
    _save("model_compare.png"); plt.show()


def plot_overfit(results):
    ax = results.set_index("model")[["train_f1", "test_f1"]].plot.bar(figsize=(9, 4), rot=15)
    ax.set_ylim(0, 1.05); ax.set_title("F1: train so với test (phát hiện overfitting)")
    _save("model_overfit.png"); plt.show()


def plot_confusion_matrices(fitted, X_test, y_test):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, (name, m) in zip(axes.ravel(), fitted.items()):
        ConfusionMatrixDisplay.from_estimator(
            m, X_test, y_test, display_labels=LABELS, ax=ax, colorbar=False)
        ax.set_title(name)
    for ax in axes.ravel()[len(fitted):]:
        ax.axis("off")
    plt.tight_layout(); _save("model_confusion.png"); plt.show()


def plot_roc(fitted, X_test, y_test):
    fig, ax = plt.subplots(figsize=(7, 6))
    for name, m in fitted.items():
        RocCurveDisplay.from_estimator(m, X_test, y_test, name=name, ax=ax)
    ax.set_title("Đường ROC (lớp ác tính)")
    _save("model_roc.png"); plt.show()