import { renameStudent } from "../_lib/students.js";
import { renameStudentInAttendanceFiles } from "../_lib/attendance.js";
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
    const result = await renameStudent(body.oldName, body.newName);

    if (!result.success) {
      return sendError(res, 400, result.message);
    }

    await renameStudentInAttendanceFiles(body.oldName, body.newName);
    return sendJson(res, 200, result);
  } catch (error) {
    console.error("students/rename error:", error);
    return sendError(res, 500, "Rename failed.");
  }
}
