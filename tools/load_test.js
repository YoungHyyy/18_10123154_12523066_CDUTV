import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const baseUrl = (__ENV.BASE_URL || "http://host.docker.internal:3000").replace(
  /\/+$/,
  "",
);
const predictErrors = new Rate("predict_errors");
const predictLatency = new Trend("predict_latency", true);

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || "1m",
  thresholds: {
    checks: ["rate>0.99"],
    predict_errors: ["rate<0.01"],
    predict_latency: ["p(95)<2000"],
  },
};

export function setup() {
  const response = http.get(`${baseUrl}/api/schema`, {
    tags: { name: "schema" },
  });
  if (response.status !== 200) {
    throw new Error(`GET /api/schema returned ${response.status}`);
  }

  const schema = response.json();
  if (!Array.isArray(schema.features) || schema.features.length !== 30) {
    throw new Error("Expected a schema containing 30 features");
  }

  const features = Object.fromEntries(
    schema.features.map((feature) => [
      feature.name,
      (feature.min + feature.max) / 2,
    ]),
  );
  return { features };
}

export default function (data) {
  const response = http.post(
    `${baseUrl}/api/predict`,
    JSON.stringify({ features: data.features }),
    {
      headers: { "Content-Type": "application/json" },
      tags: { name: "predict" },
    },
  );

  let result = {};
  try {
    result = response.json();
  } catch (_) {
    // The checks below record non-JSON responses as failures.
  }

  const valid = check(response, {
    "predict returns HTTP 200": (res) => res.status === 200,
    "response includes prediction and request ID": () =>
      typeof result.prediction === "string" &&
      typeof result.request_id === "string",
  });

  predictErrors.add(valid ? 0 : 1);
  predictLatency.add(response.timings.duration);
  sleep(1);
}
