const test = require("node:test");
const assert = require("node:assert/strict");
const { schema, validateFeatures } = require("../src/schema");

function validFeatures() {
  return Object.fromEntries(
    schema.features.map((feature) => [
      feature.name,
      (feature.min + feature.max) / 2,
    ]),
  );
}

test("accepts a complete feature object", () => {
  assert.deepEqual(validateFeatures(validFeatures()), { ok: true });
});

test("rejects missing features", () => {
  const features = validFeatures();
  delete features[schema.features[0].name];

  assert.equal(validateFeatures(features).ok, false);
  assert.match(validateFeatures(features).detail, /Thiếu cột/);
});

test("rejects extra features", () => {
  const features = { ...validFeatures(), unexpected: 1 };

  assert.equal(validateFeatures(features).ok, false);
  assert.match(validateFeatures(features).detail, /Thừa cột/);
});

test("rejects non-finite and out-of-range values", () => {
  const features = validFeatures();
  features[schema.features[0].name] = Number.POSITIVE_INFINITY;

  assert.equal(validateFeatures(features).ok, false);
});
