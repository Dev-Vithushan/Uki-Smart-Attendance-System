import { cleanupOldAttendanceFiles } from "../_lib/attendance.js";
import { sendError, sendJson } from "../_lib/http.js";

function isAuthorized(req) {
  const secret = process.env.CRON_SECRET;
  if (!secret) return true;

  const authHeader = req.headers.authorization || "";
  return authHeader === `Bearer ${secret}`;
}

export default async function handler(req, res) {
  if (req.method !== "GET" && req.method !== "POST") {
    return sendError(res, 405, "Method not allowed.");
  }

  if (!isAuthorized(req)) {
    return sendError(res, 401, "Unauthorized.");
  }

  try {
    const result = await cleanupOldAttendanceFiles();
    return sendJson(res, 200, {
      success: true,
      message: "Cleanup completed.",
      ...result,
    });
  } catch (error) {
    console.error("cron/cleanup error:", error);
    return sendError(res, 500, "Cleanup failed.");
  }
}
