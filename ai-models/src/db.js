const mongoose = require("mongoose");

async function connectDB() {
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    console.warn("Chưa có MONGODB_URI, bỏ qua kết nối DB");
    return;
  }
  await mongoose.connect(uri);
  console.log("Đã kết nối MongoDB");
}

const historySchema = new mongoose.Schema({
  requestId: String,
  features: Object,
  prediction: String,
  probability: Number,
  modelVersion: String,
  createdAt: { type: Date, default: Date.now },
});
const History = mongoose.model("History", historySchema);

module.exports = { connectDB, History };
