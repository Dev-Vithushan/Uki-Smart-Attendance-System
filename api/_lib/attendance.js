import { ATTENDANCE_HEADERS, parseAttendanceCsv, toAttendanceCsv } from "./csv.js";
import { ATTENDANCE_PREFIX, RETENTION_DAYS } from "./constants.js";
import {
  listAllByPrefix,
  getBlobText,
  putBlobText,
  deleteBlobByPath,
} from "./blobStore.js";
import {
  getMasterStudents,
  normalizeStudentName,
  findStudentByName,
} from "./students.js";

export const APP_TIMEZONE = process.env.APP_TIMEZONE || "Asia/Colombo";
export { RETENTION_DAYS };

function getNowParts() {
  const now = new Date();

  const dateFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone: APP_TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const timeFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone: APP_TIMEZONE,
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const dateParts = dateFormatter.formatToParts(now);
  const timeParts = timeFormatter.formatToParts(now);

  const byType = (parts, type) => parts.find((part) => part.type === type)?.value || "";
  const date = `${byType(dateParts, "year")}-${byType(dateParts, "month")}-${byType(
    dateParts,
    "day"
  )}`;
  const time = `${byType(timeParts, "hour")}:${byType(timeParts, "minute")}:${byType(
    timeParts,
    "second"
  )}`;

  return { date, time };
}

function shiftDate(dateString, deltaDays) {
  const date = new Date(`${dateString}T00:00:00.000Z`);
  date.setUTCDate(date.getUTCDate() + deltaDays);
  return date.toISOString().slice(0, 10);
}

function attendancePathForDate(dateString) {
  return `${ATTENDANCE_PREFIX}attendance_${dateString}.csv`;
}

function parseDateFromPath(pathname) {
  const match = pathname.match(/attendance_(\d{4}-\d{2}-\d{2})\.csv$/);
  return match ? match[1] : null;
}

function normalizeRecord(record) {
  return {
    Name: normalizeStudentName(record.Name || ""),
    Date: record.Date || "",
    Status: record.Status || "Absent",
    "Clock-In": record["Clock-In"] || "",
    "Clock-Out": record["Clock-Out"] || "",
  };
}

function getDefaultRow(name, dateString) {
  return {
    Name: name,
    Date: dateString,
    Status: "Absent",
    "Clock-In": "",
    "Clock-Out": "",
  };
}

function sanitizeRetentionDays(retentionDays) {
  const parsed = Number.parseInt(retentionDays, 10);
  if (Number.isNaN(parsed) || parsed < 1) return RETENTION_DAYS;
  return parsed;
}

function byNameMap(records) {
  const map = new Map();
  for (const record of records) {
    const key = normalizeStudentName(record.Name).toLowerCase();
    if (!key) continue;
    map.set(key, normalizeRecord(record));
  }
  return map;
}

function buildAttendanceSummary(rows, students) {
  const normalizedRows = rows.map(normalizeRecord);
  const records = normalizedRows.filter((row) => row.Status === "Present");
  const absentNames = normalizedRows
    .filter((row) => row.Status !== "Present")
    .map((row) => row.Name)
    .sort();

  const totalRegistered = students.length;
  const totalPresent = records.length;
  const percentage =
    totalRegistered > 0 ? Number(((totalPresent / totalRegistered) * 100).toFixed(1)) : 0;

  return {
    records,
    absent_names: absentNames,
    stats: {
      total_registered: totalRegistered,
      total_present: totalPresent,
      percentage,
    },
  };
}

export async function cleanupOldAttendanceFiles(retentionDays = RETENTION_DAYS) {
  const effectiveRetention = sanitizeRetentionDays(retentionDays);
  const today = getNowParts().date;
  const cutoffDate = shiftDate(today, -(effectiveRetention - 1));

  const blobs = await listAllByPrefix(ATTENDANCE_PREFIX);
  const deletedFiles = [];

  for (const blob of blobs) {
    const dateString = parseDateFromPath(blob.pathname);
    if (!dateString) continue;

    if (dateString < cutoffDate) {
      await deleteBlobByPath(blob.pathname);
      deletedFiles.push(blob.pathname);
    }
  }

  return {
    retentionDays: effectiveRetention,
    cutoffDate,
    deletedFiles,
  };
}

async function ensureAttendanceFileForDate(dateString, students, options = {}) {
  const writeChanges = options.writeChanges === true;

  const path = attendancePathForDate(dateString);
  const csv = await getBlobText(path);
  const existingRecords = parseAttendanceCsv(csv || "");
  const existingByName = byNameMap(existingRecords);

  const mergedRows = students.map((student) => {
    const key = student.name.toLowerCase();
    const fromExisting = existingByName.get(key);
    if (!fromExisting) {
      return getDefaultRow(student.name, dateString);
    }

    return {
      ...getDefaultRow(student.name, dateString),
      ...fromExisting,
      Name: student.name,
      Date: dateString,
    };
  });

  const nextCsv = toAttendanceCsv(mergedRows);
  if (writeChanges) {
    await putBlobText(path, nextCsv, "text/csv; charset=utf-8");
  }

  return { path, rows: mergedRows, csv: nextCsv };
}

export async function ensureTodayAttendanceFile(options = {}) {
  await cleanupOldAttendanceFiles();
  const students = await getMasterStudents();
  const { date } = getNowParts();
  return ensureAttendanceFileForDate(date, students, {
    writeChanges: options.writeChanges !== false,
  });
}

export async function getTodayAttendanceSummary() {
  const students = await getMasterStudents();
  const { date } = getNowParts();
  const { rows } = await ensureAttendanceFileForDate(date, students, {
    writeChanges: false,
  });
  return buildAttendanceSummary(rows, students);
}

export async function updateAttendance(type, name, override = false) {
  const normalizedName = normalizeStudentName(name);
  if (!normalizedName) {
    return { success: false, message: "No recognized face.", is_conflict: false };
  }

  const students = await getMasterStudents();
  const student = findStudentByName(students, normalizedName);
  if (!student) {
    return { success: false, message: `${normalizedName} is not a registered student.`, is_conflict: false };
  }

  const { date, time } = getNowParts();
  const { path, rows } = await ensureAttendanceFileForDate(date, students, {
    writeChanges: false,
  });
  const index = rows.findIndex((row) => row.Name.toLowerCase() === student.name.toLowerCase());

  if (index < 0) {
    return { success: false, message: `No attendance row found for ${student.name}.`, is_conflict: false };
  }

  const current = rows[index];

  if (type === "clock_in") {
    if (current.Status === "Present" && current["Clock-In"] && !override) {
      return {
        success: false,
        message: `Already clocked in at ${current["Clock-In"]}.`,
        is_conflict: true,
      };
    }

    rows[index] = {
      ...current,
      Name: student.name,
      Date: date,
      Status: "Present",
      "Clock-In": time,
    };
  } else {
    const alreadyOut = current["Clock-Out"] && current["Clock-Out"].trim() !== "";
    if (alreadyOut && !override) {
      return {
        success: false,
        message: `Already clocked out at ${current["Clock-Out"]}.`,
        is_conflict: true,
      };
    }

    rows[index] = {
      ...current,
      Name: student.name,
      Date: date,
      Status: "Present",
      "Clock-Out": time,
    };
  }

  const nextCsv = toAttendanceCsv(rows);
  await putBlobText(path, nextCsv, "text/csv; charset=utf-8");

  return {
    success: true,
    is_conflict: false,
    message:
      type === "clock_in"
        ? override
          ? `Clock-in overridden to ${time}.`
          : `Successfully clocked in at ${time}.`
        : override
          ? `Clock-out overridden to ${time}.`
          : `Successfully clocked out at ${time}.`,
    summary: buildAttendanceSummary(rows, students),
  };
}

export async function listAttendanceFiles(limitDays = RETENTION_DAYS) {
  await cleanupOldAttendanceFiles(limitDays);
  const effectiveLimit = sanitizeRetentionDays(limitDays);

  const today = getNowParts().date;
  const cutoffDate = shiftDate(today, -(effectiveLimit - 1));
  const blobs = await listAllByPrefix(ATTENDANCE_PREFIX);

  const files = blobs
    .map((blob) => {
      const date = parseDateFromPath(blob.pathname);
      if (!date) return null;

      if (date < cutoffDate) return null;

      return {
        date,
        filename: blob.pathname.split("/").pop(),
        pathname: blob.pathname,
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.date.localeCompare(a.date));

  return {
    files,
    retentionDays: effectiveLimit,
  };
}

export async function downloadAttendanceCsv(dateString) {
  const date = String(dateString || "").trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return null;
  }

  const today = getNowParts().date;
  if (date === today) {
    const { csv } = await ensureTodayAttendanceFile({ writeChanges: false });
    return {
      date,
      csv,
      filename: `attendance_${date}_google_sheets.csv`,
    };
  }

  const path = attendancePathForDate(date);
  const csv = await getBlobText(path);
  if (csv === null) return null;

  return {
    date,
    csv,
    filename: `attendance_${date}_google_sheets.csv`,
  };
}

export async function renameStudentInAttendanceFiles(oldName, newName) {
  const previous = normalizeStudentName(oldName);
  const next = normalizeStudentName(newName);
  if (!previous || !next) return;

  const { files } = await listAttendanceFiles(RETENTION_DAYS);

  for (const file of files) {
    const csv = await getBlobText(file.pathname);
    if (csv === null) continue;

    const rows = parseAttendanceCsv(csv).map(normalizeRecord);
    let changed = false;

    for (const row of rows) {
      if (normalizeStudentName(row.Name).toLowerCase() === previous.toLowerCase()) {
        row.Name = next;
        changed = true;
      }
    }

    if (changed) {
      await putBlobText(file.pathname, toAttendanceCsv(rows), "text/csv; charset=utf-8");
    }
  }
}

export async function deleteStudentFromAttendanceFiles(name) {
  const normalized = normalizeStudentName(name);
  if (!normalized) return;

  const { files } = await listAttendanceFiles(RETENTION_DAYS);
  for (const file of files) {
    const csv = await getBlobText(file.pathname);
    if (csv === null) continue;

    const rows = parseAttendanceCsv(csv)
      .map(normalizeRecord)
      .filter((row) => normalizeStudentName(row.Name).toLowerCase() !== normalized.toLowerCase());

    await putBlobText(file.pathname, toAttendanceCsv(rows), "text/csv; charset=utf-8");
  }
}
