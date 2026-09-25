const mongoose = require("mongoose");
let dbStatus = "not_configured";

async function connectDB() {
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    dbStatus = "not_configured";
    console.warn("Chưa có MONGODB_URI, bỏ qua kết nối DB");
    return false;
  }

  dbStatus = "connecting";
  try {
    await mongoose.connect(uri, { serverSelectionTimeoutMS: 5000 });
  } catch (error) {
    dbStatus = "error";
    throw error;
  }
  dbStatus = "connected";
  console.log("Đã kết nối MongoDB");
  return true;
}

mongoose.connection.on("disconnected", () => {
  dbStatus = "disconnected";
});

mongoose.connection.on("error", () => {
  dbStatus = "error";
});

const historySchema = new mongoose.Schema({
  requestId: { type: String, required: true, index: true },
  features: { type: Object, required: true },
  prediction: { type: String, required: true },
  probability: { type: Number, required: true },
  modelVersion: { type: String, required: true },
  createdAt: { type: Date, default: Date.now, index: true },
});

const History =
  mongoose.models.History || mongoose.model("History", historySchema);

module.exports = { connectDB, getDbStatus: () => dbStatus, History, mongoose };
