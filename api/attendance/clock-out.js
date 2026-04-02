import { updateAttendance } from "../_lib/attendance.js";
import {
  sendError,
  sendJson,
  methodNotAllowed,
  getRequestBody,
} from "../_lib/http.js";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return methodNotAllowed(res, ["POST"]);
  }

  try {
    const body = getRequestBody(req);
    const result = await updateAttendance("clock_out", body.name, Boolean(body.override));

    if (!result.success) {
      const statusCode = result.is_conflict ? 409 : 400;
      return sendError(res, statusCode, result.message, {
        is_conflict: Boolean(result.is_conflict),
      });
    }

    return sendJson(res, 200, result);
  } catch (error) {
    console.error("attendance/clock-out error:", error);
    return sendError(res, 500, "Clock-out failed.");
  }
}
