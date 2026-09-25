require("dotenv").config();
const express = require("express");
const cors = require("cors");
const { connectDB } = require("./db");
const predictRoutes = require("./routes/predict");

const app = express();
app.use(cors());
app.use(express.json());

const START_TIME = Date.now();
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    uptime_seconds: Math.round((Date.now() - START_TIME) / 1000),
  });
});

app.use("/api", predictRoutes);

const PORT = process.env.PORT || 8000;
connectDB().finally(() => {
  app.listen(PORT, () => console.log(`Backend chạy ở cổng ${PORT}`));
});
