const DEFAULT_RETENTION_DAYS = 15;
const DEFAULT_FACE_MATCH_THRESHOLD = 0.5;

function readIntEnv(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;

  const parsed = Number.parseInt(raw, 10);
  if (Number.isNaN(parsed) || parsed < 1) return fallback;
  return parsed;
}

function readFloatEnv(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;

  const parsed = Number.parseFloat(raw);
  if (Number.isNaN(parsed) || parsed <= 0) return fallback;
  return parsed;
}

export const RETENTION_DAYS = readIntEnv(
  "LOG_RETENTION_DAYS",
  DEFAULT_RETENTION_DAYS
);
export const FACE_MATCH_THRESHOLD = readFloatEnv(
  "FACE_MATCH_THRESHOLD",
  DEFAULT_FACE_MATCH_THRESHOLD
);

export const MASTER_FILE_PATH = "students/master.json";
export const STUDENT_IMAGES_PREFIX = "students/images/";
export const ATTENDANCE_PREFIX = "attendance/";
