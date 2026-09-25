process.env.PORT = "0";
process.env.MONGODB_URI = "";

process.env.AI_SERVICE_URL = "http://127.0.0.1:1";
const test = require("node:test");
const assert = require("node:assert/strict");
const { start } = require("../src/server");

let server;
let baseUrl;

function validFeatures(schema) {
  return Object.fromEntries(
    schema.features.map((feature) => [
      feature.name,
      (feature.min + feature.max) / 2,
    ]),
  );
}

test.before(async () => {
  server = await start();
  baseUrl = `http://127.0.0.1:${server.address().port}`;
});

test.after(() => server.close());

test("health reports backend status", async () => {
  const response = await fetch(`${baseUrl}/health`);
  const body = await response.json();

  assert.equal(response.status, 200);
  assert.equal(body.service, "backend");
  assert.equal(body.status, "ok");
  assert.ok(body.database);
});

test("schema endpoint exposes the model contract", async () => {
  const response = await fetch(`${baseUrl}/api/schema`);
  const body = await response.json();

  assert.equal(response.status, 200);
  assert.equal(body.features.length, 30);
  assert.equal(body.target, "diagnosis");
});

test("predict rejects malformed input before calling AI Service", async () => {
  const response = await fetch(`${baseUrl}/api/predict`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ features: {} }),
  });
  const body = await response.json();

  assert.equal(response.status, 400);
  assert.equal(body.error, "invalid_input");
  assert.ok(body.request_id);
});

test("predict returns 502 when AI Service is unavailable", async () => {
  const { schema } = require("../src/schema");
  const response = await fetch(`${baseUrl}/api/predict`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ features: validFeatures(schema) }),
  });
  const body = await response.json();

  assert.equal(response.status, 502);
  assert.equal(body.error, "ai_service_unreachable");
  assert.ok(body.request_id);
});
