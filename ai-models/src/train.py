"""Huấn luyện baseline + 4 model, cùng cách chia dữ liệu, cùng metric."""
import tempfile
import time
import warnings
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from preprocess import MODELS_DIR, RANDOM_STATE, make_preprocessor


def get_candidates():
    """Tên -> (model, lưới siêu tham số). Khóa lưới bắt đầu bằng clf__.
    Chỉ dùng các model có trong chương trình môn học."""
    return {
        "Logistic Regression (baseline)": (
            LogisticRegression(max_iter=5000, class_weight="balanced",
                               random_state=RANDOM_STATE),
            {"clf__C": [0.01, 0.1, 1, 10, 100]}),
        "KNN": (
            KNeighborsClassifier(),
            {"clf__n_neighbors": [3, 5, 7, 9, 11, 15],
             "clf__weights": ["uniform", "distance"]}),
        "SVM (RBF)": (
            SVC(kernel="rbf", probability=True, class_weight="balanced",
                random_state=RANDOM_STATE),
            {"clf__C": [0.1, 1, 10, 100], "clf__gamma": ["scale", 0.01, 0.1]}),
        "Decision Tree": (
            DecisionTreeClassifier(class_weight="balanced", random_state=RANDOM_STATE),
            {"clf__criterion": ["gini", "entropy"],
             "clf__max_depth": [3, 5, 7, 10, None],
             "clf__min_samples_leaf": [1, 2, 5]}),
        "Random Forest": (
            RandomForestClassifier(class_weight="balanced",
                                   random_state=RANDOM_STATE, n_jobs=-1),
            {"clf__n_estimators": [100, 200, 300],
             "clf__max_depth": [None, 5, 10],
             "clf__min_samples_leaf": [1, 2]}),
    }


def compute_metrics(model, X, y):
    pred = model.predict(X)
    proba = model.predict_proba(X)[:, 1]
    return {
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred),          # lớp dương = ác tính
        "f1": f1_score(y, pred),
        "roc_auc": roc_auc_score(y, proba),
        "pr_auc": average_precision_score(y, proba),
    }


def _size_kb(model):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "m.joblib"
        joblib.dump(model, p, compress=3)
        return round(p.stat().st_size / 1024, 1)


def run_experiments(X_train, X_test, y_train, y_test):
    """Tinh chỉnh bằng CV trên tập train; chỉ dùng tập test MỘT lần cho kết quả cuối."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    rows, fitted = [], {}
    for name, (est, grid) in get_candidates().items():
        print(f">>> {name}")
        pipe = Pipeline([("prep", make_preprocessor()), ("clf", est)])
        gs = GridSearchCV(pipe, grid, cv=cv, scoring="f1", n_jobs=-1)
        t0 = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gs.fit(X_train, y_train)
        fit_s = time.perf_counter() - t0
        best = gs.best_estimator_

        t0 = time.perf_counter()
        best.predict(X_test)
        pred_ms = (time.perf_counter() - t0) / len(X_test) * 1000   # ms / mẫu

        tr, te = compute_metrics(best, X_train, y_train), compute_metrics(best, X_test, y_test)
        rows.append({
            "model": name,
            "best_params": {k.replace("clf__", ""): v for k, v in gs.best_params_.items()},
            "cv_f1_mean": gs.cv_results_["mean_test_score"][gs.best_index_],
            "cv_f1_std": gs.cv_results_["std_test_score"][gs.best_index_],
            "train_recall": tr["recall"], "train_f1": tr["f1"],
            "test_recall": te["recall"], "test_precision": te["precision"],
            "test_f1": te["f1"], "test_accuracy": te["accuracy"],
            "test_roc_auc": te["roc_auc"], "test_pr_auc": te["pr_auc"],
            "fit_seconds": round(fit_s, 1), "predict_ms_per_sample": round(pred_ms, 3),
            "size_kb": _size_kb(best),
        })
        fitted[name] = best
    return pd.DataFrame(rows).round(4), fitted


def save_candidates(fitted, folder=MODELS_DIR / "candidates"):
    folder.mkdir(parents=True, exist_ok=True)
    for name, model in fitted.items():
        slug = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        joblib.dump(model, folder / f"{slug}.joblib", compress=3)