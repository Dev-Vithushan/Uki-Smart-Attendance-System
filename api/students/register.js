import { registerStudent } from "../_lib/students.js";
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
    const result = await registerStudent({
      name: body.name,
      imageDataUrl: body.imageDataUrl,
      descriptor: body.descriptor,
    });

    if (!result.success) {
      return sendError(res, 400, result.message);
    }

    return sendJson(res, 200, result);
  } catch (error) {
    console.error("students/register error:", error);
    return sendError(res, 500, "Registration failed.");
  }
}
