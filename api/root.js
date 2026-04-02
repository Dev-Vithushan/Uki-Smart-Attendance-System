import fs from "node:fs";
import path from "node:path";
import { methodNotAllowed } from "./_lib/http.js";

const INDEX_PATH = path.join(process.cwd(), "index.html");

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return methodNotAllowed(res, ["GET"]);
  }

  try {
    const html = fs.readFileSync(INDEX_PATH, "utf8");
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    return res.status(200).send(html);
  } catch (error) {
    console.error("root handler error:", error);
    return res.status(500).json({
      success: false,
      message: "Failed to load UI.",
    });
  }
}
