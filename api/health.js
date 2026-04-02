import { sendJson, methodNotAllowed } from "./_lib/http.js";

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return methodNotAllowed(res, ["GET"]);
  }

  return sendJson(res, 200, {
    success: true,
    message: "OK",
    timestamp: new Date().toISOString(),
  });
}
