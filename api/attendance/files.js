import { listAttendanceFiles, RETENTION_DAYS } from "../_lib/attendance.js";
import { sendError, sendJson, methodNotAllowed } from "../_lib/http.js";

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return methodNotAllowed(res, ["GET"]);
  }

  try {
    const parsed = Number.parseInt(req.query.limit_days, 10);
    const limitDays = Number.isNaN(parsed) ? RETENTION_DAYS : parsed;
    const payload = await listAttendanceFiles(limitDays);
    return sendJson(res, 200, payload);
  } catch (error) {
    console.error("attendance/files error:", error);
    return sendError(res, 500, "Failed to load attendance files.");
  }
}
