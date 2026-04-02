import { downloadAttendanceCsv } from "../_lib/attendance.js";
import { sendError, methodNotAllowed } from "../_lib/http.js";

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return methodNotAllowed(res, ["GET"]);
  }

  try {
    const date = req.query.date;
    if (!date) {
      return sendError(res, 400, "Query parameter 'date' is required.");
    }

    const file = await downloadAttendanceCsv(date);
    if (!file) {
      return sendError(res, 404, `No attendance file found for ${date}.`);
    }

    res.setHeader("Content-Type", "text/csv; charset=utf-8");
    res.setHeader(
      "Content-Disposition",
      `attachment; filename="${file.filename}"`
    );
    return res.status(200).send(`\uFEFF${file.csv}`);
  } catch (error) {
    console.error("attendance/download error:", error);
    return sendError(res, 500, "Failed to download attendance file.");
  }
}
