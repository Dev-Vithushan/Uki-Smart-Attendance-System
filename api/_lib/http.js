export function sendJson(res, statusCode, payload) {
  res.status(statusCode).json(payload);
}

export function sendError(res, statusCode, message, extras = {}) {
  sendJson(res, statusCode, {
    success: false,
    message,
    ...extras,
  });
}

export function methodNotAllowed(res, allowed) {
  res.setHeader("Allow", allowed.join(", "));
  sendError(res, 405, `Method not allowed. Use: ${allowed.join(", ")}.`);
}

export function getRequestBody(req) {
  if (typeof req.body === "string") {
    try {
      return JSON.parse(req.body);
    } catch (_error) {
      return {};
    }
  }

  if (req.body && typeof req.body === "object") {
    return req.body;
  }

  return {};
}
