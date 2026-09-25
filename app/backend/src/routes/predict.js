const express = require("express");
const axios = require("axios");
const { v4: uuidv4 } = require("uuid");
const { History, mongoose } = require("../db");
const { schema, validateFeatures } = require("../schema");

const router = express.Router();
const aiServiceUrl = process.env.AI_SERVICE_URL || "http://ai-service:8001";
const aiClient = axios.create({ baseURL: aiServiceUrl, timeout: 5000 });

function invalidInput(res, requestId, detail) {
  return res.status(400).json({
    error: "invalid_input",
    detail,
    request_id: requestId,
  });
}

router.post("/predict", async (req, res) => {
  const requestId = req.requestId || uuidv4().slice(0, 8);
  const startedAt = Date.now();
  const validation = validateFeatures(req.body?.features);
  if (!validation.ok) {
    console.log(`req=${requestId} 400 ${validation.detail}`);
    return invalidInput(res, requestId, validation.detail);
  }

  try {
    console.log(`req=${requestId} validate OK -> gọi ai-service`);
    const aiResponse = await aiClient.post(
      "/predict",
      { features: req.body.features },
      { headers: { "x-request-id": requestId } },
    );
    const {
      prediction,
      probability,
      model_version: modelVersion,
    } = aiResponse.data;

    if (mongoose.connection.readyState === 1) {
      await History.create({
        requestId,
        features: req.body.features,
        prediction,
        probability,
        modelVersion,
      }).catch((error) =>
        console.error(`req=${requestId} lỗi lưu lịch sử:`, error.message),
      );
    }

    console.log(`req=${requestId} 200 OK total ${Date.now() - startedAt}ms`);
    return res.json({
      prediction,
      probability,
      model_version: modelVersion,
      request_id: requestId,
    });
  } catch (error) {
    if (error.response) {
      console.log(
        `req=${requestId} ${error.response.status} lỗi từ ai-service`,
      );
      return res.status(error.response.status).json({
        ...error.response.data,
        request_id: requestId,
      });
    }

    console.error(
      `req=${requestId} 502 không gọi được ai-service:`,
      error.message,
    );
    return res.status(502).json({
      error: "ai_service_unreachable",
      detail: "Không thể kết nối AI Service",
      request_id: requestId,
    });
  }
});

router.get("/history", async (req, res) => {
  if (mongoose.connection.readyState !== 1) {
    return res.json([]);
  }

  try {
    const items = await History.find().sort({ createdAt: -1 }).limit(50).lean();
    return res.json(items);
  } catch (error) {
    console.error("Lỗi đọc lịch sử:", error.message);
    return res
      .status(500)
      .json({ error: "history_unavailable", detail: "Không thể đọc lịch sử" });
  }
});

router.get("/schema", (req, res) => res.json(schema));

router.get("/model-info", async (req, res) => {
  try {
    const response = await aiClient.get("/model-info");
    return res.json(response.data);
  } catch (error) {
    return res.status(502).json({
      error: "ai_service_unreachable",
      detail: "Không thể lấy thông tin model",
    });
  }
});

module.exports = router;
