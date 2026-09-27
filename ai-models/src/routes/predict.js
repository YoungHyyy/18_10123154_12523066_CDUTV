const express = require("express");
const axios = require("axios");
const { v4: uuidv4 } = require("uuid");
const { History } = require("../db");

const router = express.Router();
const AI_SERVICE_URL = process.env.AI_SERVICE_URL;

router.post("/predict", async (req, res) => {
  const requestId = uuidv4().slice(0, 8);
  const t0 = Date.now();
  const { features } = req.body;

  if (!features || typeof features !== "object") {
    console.log(`req=${requestId} 400 thiếu features`);
    return res.status(400).json({
      error: "invalid_input",
      detail: "Thiếu trường features",
      request_id: requestId,
    });
  }

  if (!AI_SERVICE_URL) {
    return res.status(503).json({
      error: "configuration_error",
      detail: "AI_SERVICE_URL chưa được cấu hình",
      request_id: requestId,
    });
  }

  try {
    console.log(`req=${requestId} validate OK -> gọi ai-service`);
    const aiRes = await axios.post(
      `${AI_SERVICE_URL}/predict`,
      { features },
      { headers: { "x-request-id": requestId }, timeout: 5000 },
    );

    const { prediction, probability, model_version } = aiRes.data;

    await History.create({
      requestId,
      features,
      prediction,
      probability,
      modelVersion: model_version,
    }).catch((e) =>
      console.error(`req=${requestId} lỗi lưu lịch sử:`, e.message),
    );

    console.log(`req=${requestId} 200 OK total ${Date.now() - t0}ms`);
    res.json({ prediction, probability, model_version, request_id: requestId });
  } catch (err) {
    if (err.response) {
      console.log(`req=${requestId} ${err.response.status} lỗi từ ai-service`);
      return res
        .status(err.response.status)
        .json({ ...err.response.data, request_id: requestId });
    }
    console.error(
      `req=${requestId} 5xx không gọi được ai-service:`,
      err.message,
    );
    res.status(502).json({
      error: "ai_service_unreachable",
      detail: err.message,
      request_id: requestId,
    });
  }
});

router.get("/history", async (req, res) => {
  const items = await History.find().sort({ createdAt: -1 }).limit(50);
  res.json(items);
});

module.exports = router;
