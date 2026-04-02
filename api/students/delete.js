import { deleteStudent } from "../_lib/students.js";
import { deleteStudentFromAttendanceFiles } from "../_lib/attendance.js";
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
    const result = await deleteStudent(body.name);

    if (!result.success) {
      return sendError(res, 400, result.message);
    }

    await deleteStudentFromAttendanceFiles(body.name);
    return sendJson(res, 200, result);
  } catch (error) {
    console.error("students/delete error:", error);
    return sendError(res, 500, "Delete failed.");
  }
}
