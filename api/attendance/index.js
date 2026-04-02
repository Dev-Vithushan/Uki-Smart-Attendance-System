import { getTodayAttendanceSummary } from "../_lib/attendance.js";
import { sendError, sendJson, methodNotAllowed } from "../_lib/http.js";

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return methodNotAllowed(res, ["GET"]);
  }

  try {
    const payload = await getTodayAttendanceSummary();
    return sendJson(res, 200, payload);
  } catch (error) {
    console.error("attendance/index error:", error);
    return sendError(res, 500, "Failed to load attendance.");
  }
}
