require("dotenv").config();

const express = require("express");
const cors = require("cors");
const { v4: uuidv4 } = require("uuid");
const { connectDB, getDbStatus } = require("./db");
const predictRoutes = require("./routes/predict");

const app = express();
const port = Number(process.env.PORT || 8000);
const startTime = Date.now();

app.use(cors({ origin: process.env.CORS_ORIGIN || true }));
app.use(express.json({ limit: "100kb" }));
app.use((req, res, next) => {
  req.requestId = req.get("x-request-id") || uuidv4().slice(0, 8);
  res.setHeader("x-request-id", req.requestId);
  const startedAt = Date.now();
  res.on("finish", () => {
    console.log(
      `req=${req.requestId} ${req.method} ${req.originalUrl} -> ${res.statusCode} in ${Date.now() - startedAt}ms`,
    );
  });
  next();
});

app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "backend",
    port,
    database: getDbStatus(),
    uptime_seconds: Math.round((Date.now() - startTime) / 1000),
  });
});

app.use("/api", predictRoutes);

app.use((error, req, res, next) => {
  if (error instanceof SyntaxError && error.status === 400 && "body" in error) {
    return res.status(400).json({
      error: "invalid_input",
      detail: "JSON request không hợp lệ",
      request_id: req.requestId,
    });
  }
  console.error(`req=${req.requestId || "unknown"} lỗi không xử lý:`, error);
  return res
    .status(500)
    .json({ error: "internal_error", request_id: req.requestId });
});

async function start() {
  try {
    await connectDB();
  } catch (error) {
    console.error(
      "Không thể kết nối MongoDB, tiếp tục không có history:",
      error.message,
    );
  }
  return app.listen(port, () => console.log(`Backend chạy ở cổng ${port}`));
}

if (require.main === module) {
  start();
}

module.exports = { app, start };
