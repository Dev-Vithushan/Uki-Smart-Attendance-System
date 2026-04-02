import { listStudents } from "../_lib/students.js";
import { sendError, sendJson, methodNotAllowed } from "../_lib/http.js";

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return methodNotAllowed(res, ["GET"]);
  }

  try {
    const students = await listStudents();
    return sendJson(res, 200, { students });
  } catch (error) {
    console.error("students/index error:", error);
    return sendError(res, 500, "Failed to load students.");
  }
}
