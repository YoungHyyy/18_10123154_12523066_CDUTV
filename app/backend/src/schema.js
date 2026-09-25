const fs = require("node:fs");
const path = require("node:path");

const schemaPath =
  process.env.SCHEMA_PATH ||
  path.resolve(__dirname, "../../../ai-models/models/schema.json");
const schema = JSON.parse(fs.readFileSync(schemaPath, "utf8"));
const featureDefinitions = new Map(
  schema.features.map((feature) => [feature.name, feature]),
);

function validateFeatures(features) {
  if (!features || typeof features !== "object" || Array.isArray(features)) {
    return { ok: false, detail: "Trường features phải là một object" };
  }

  const missing = schema.features
    .map((feature) => feature.name)
    .filter((name) => !(name in features));
  if (missing.length > 0) {
    return { ok: false, detail: `Thiếu cột: ${missing.join(", ")}` };
  }

  const extra = Object.keys(features).filter(
    (name) => !featureDefinitions.has(name),
  );
  if (extra.length > 0) {
    return { ok: false, detail: `Thừa cột: ${extra.join(", ")}` };
  }

  const invalid = [];
  for (const feature of schema.features) {
    const value = features[feature.name];
    if (
      typeof value !== "number" ||
      !Number.isFinite(value) ||
      value < feature.min ||
      value > feature.max
    ) {
      invalid.push(feature.name);
    }
  }
  if (invalid.length > 0) {
    return {
      ok: false,
      detail: `Giá trị ngoài khoảng hợp lệ hoặc không hữu hạn: ${invalid.join(", ")}`,
    };
  }

  return { ok: true };
}

module.exports = { schema, validateFeatures };
