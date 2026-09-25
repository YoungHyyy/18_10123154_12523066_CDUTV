const state = { schema: null, modelInfo: null };
const $ = (selector) => document.querySelector(selector);

async function getJson(url) {
  const response = await fetch(url);
  const body = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(
      body.detail || body.error || `Yêu cầu thất bại: ${response.status}`,
    );
  return body;
}

function prettyName(name) {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function groupForFeature(name) {
  if (name.endsWith("_se")) return "Sai số chuẩn";
  if (name.endsWith("_worst")) return "Giá trị xấu nhất";
  return "Giá trị trung bình";
}

function renderFields(schema) {
  const groups = new Map([
    ["Giá trị trung bình", []],
    ["Sai số chuẩn", []],
    ["Giá trị xấu nhất", []],
  ]);
  schema.features.forEach((feature) =>
    groups.get(groupForFeature(feature.name)).push(feature),
  );
  $("#field-groups").innerHTML = [...groups]
    .map(
      ([title, features]) => `
    <fieldset class="feature-group">
      <legend>${title}<span>${features.length} chỉ số</span></legend>
      <div class="feature-grid">
        ${features
          .map((feature) => {
            const midpoint = ((feature.min + feature.max) / 2).toPrecision(7);
            return `<label class="field" for="${feature.name}">
            <span>${prettyName(feature.name)}</span>
            <input id="${feature.name}" name="${feature.name}" type="number" inputmode="decimal" step="any" min="${feature.min}" max="${feature.max}" value="${midpoint}" required />
            <small>${feature.min} - ${feature.max}</small>
          </label>`;
          })
          .join("")}
      </div>
    </fieldset>`,
    )
    .join("");
  $("#predict-button").disabled = false;
}

function renderModelInfo(info) {
  state.modelInfo = info;
  $("#model-name").textContent = info.model_name;
  $("#model-version").textContent =
    `v${info.model_version} | huấn luyện ${info.trained_on}`;
  const metrics = info.metrics || {};
  $("#metrics-list").innerHTML = Object.entries(metrics)
    .map(
      ([name, value]) => `
    <div class="metric-row"><span>${metricLabel(name)}</span><strong>${Number(value).toFixed(4)}</strong></div>`,
    )
    .join("");
}

function setSystemState(stateName, label) {
  $("#system-state").dataset.state = stateName;
  $("#system-state-label").textContent = label;
}

function showError(message) {
  $("#form-note").textContent = message;
  $("#form-note").classList.add("error-text");
}

function clearError() {
  $("#form-note").classList.remove("error-text");
  $("#form-note").textContent =
    "Giá trị sẽ được kiểm tra theo schema của mô hình.";
}

function metricLabel(name) {
  const labels = {
    test_recall: "Recall trên tập test",
    test_precision: "Precision trên tập test",
    test_f1: "F1 trên tập test",
    test_roc_auc: "ROC-AUC trên tập test",
  };
  return labels[name] || prettyName(name);
}

function predictionLabel(prediction) {
  return prediction === "malignant" ? "Ác tính" : "Lành tính";
}

function renderResult(result) {
  const isMalignant = result.prediction === "malignant";
  const percent = (Number(result.probability) * 100).toFixed(1);
  $("#result-title").textContent = isMalignant
    ? "Cần xem xét"
    : "Tín hiệu nguy cơ thấp";
  $("#result-value").textContent = predictionLabel(result.prediction);
  $("#result-value").className =
    `result-value ${isMalignant ? "malignant" : "benign"}`;
  $("#result-icon").textContent = isMalignant ? "!" : "✓";
  $("#result-icon").className =
    `result-icon ${isMalignant ? "malignant" : "benign"}`;
  $("#result-copy").textContent = isMalignant
    ? "Mô hình nhận diện lớp ác tính. Hãy xem xét kết quả cùng bối cảnh lâm sàng."
    : "Mô hình nhận diện lớp lành tính cho hồ sơ này.";
  $("#probability-value").textContent = `${percent}%`;
  $("#probability-bar").style.width = `${percent}%`;
  $("#request-meta").textContent =
    `Yêu cầu ${result.request_id || "--"} | mô hình ${result.model_version || "--"}`;
}

function renderHistory(items) {
  if (!items.length) {
    $("#history-body").innerHTML =
      '<tr><td colspan="4" class="empty-state">Chưa có dự đoán nào.</td></tr>';
    return;
  }
  $("#history-body").innerHTML = items
    .map(
      (item) => `<tr>
    <td>${new Date(item.createdAt).toLocaleString("vi-VN")}</td>
    <td><span class="table-badge ${item.prediction}">${predictionLabel(item.prediction)}</span></td>
    <td>${(Number(item.probability) * 100).toFixed(1)}%</td>
    <td>${item.modelVersion || "--"}</td>
  </tr>`,
    )
    .join("");
}

async function loadHistory() {
  try {
    renderHistory(await getJson("/api/history"));
  } catch (error) {
    $("#history-body").innerHTML =
      `<tr><td colspan="4" class="empty-state error-text">Không tải được lịch sử: ${error.message}</td></tr>`;
  }
}

async function submitPrediction(event) {
  event.preventDefault();
  clearError();
  const button = $("#predict-button");
  button.disabled = true;
  button.classList.add("is-loading");
  button.querySelector("span").textContent = "Đang xử lý...";
  const features = Object.fromEntries(
    new FormData(event.currentTarget).entries(),
  );
  Object.keys(features).forEach((key) => {
    features[key] = Number(features[key]);
  });
  try {
    renderResult(
      await (async () => {
        const response = await fetch("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ features }),
        });
        const body = await response.json();
        if (!response.ok)
          throw new Error(body.detail || body.error || "Dự đoán thất bại");
        return body;
      })(),
    );
    setSystemState("ready", "Hệ thống sẵn sàng");
    await loadHistory();
  } catch (error) {
    showError(error.message);
    setSystemState("error", "Lỗi dịch vụ");
  } finally {
    button.disabled = false;
    button.classList.remove("is-loading");
    button.querySelector("span").textContent = "Dự đoán";
  }
}

async function boot() {
  try {
    const [schema, modelInfo] = await Promise.all([
      getJson("/api/schema"),
      getJson("/api/model-info"),
    ]);
    state.schema = schema;
    renderFields(schema);
    renderModelInfo(modelInfo);
    setSystemState("ready", "Hệ thống sẵn sàng");
    await loadHistory();
  } catch (error) {
    setSystemState("error", "Backend không khả dụng");
    $("#field-groups").innerHTML =
      `<div class="empty-state error-text">${error.message}</div>`;
    $("#metrics-list").innerHTML =
      '<div class="empty-state">Không tải được metric mô hình.</div>';
  }
}

$("#prediction-form").addEventListener("submit", submitPrediction);
$("#reset-button").addEventListener("click", () => {
  $("#prediction-form").reset();
  clearError();
});
$("#refresh-history").addEventListener("click", loadHistory);
boot();
