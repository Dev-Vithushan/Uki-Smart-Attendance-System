export const ATTENDANCE_HEADERS = ["Name", "Date", "Status", "Clock-In", "Clock-Out"];

function normalizeCell(value) {
  if (value === null || value === undefined) return "";
  return String(value);
}

function escapeCsvCell(value) {
  const text = normalizeCell(value);
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function toAttendanceCsv(rows) {
  const lines = [ATTENDANCE_HEADERS.join(",")];
  for (const row of rows) {
    const line = ATTENDANCE_HEADERS.map((header) =>
      escapeCsvCell(row[header] || "")
    ).join(",");
    lines.push(line);
  }
  return lines.join("\n");
}

function parseCsvRows(csvText) {
  const rows = [];
  let currentCell = "";
  let currentRow = [];
  let inQuotes = false;

  const text = (csvText || "").replace(/^\uFEFF/, "");

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (inQuotes) {
      if (char === '"' && next === '"') {
        currentCell += '"';
        i += 1;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        currentCell += char;
      }
      continue;
    }

    if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      currentRow.push(currentCell);
      currentCell = "";
    } else if (char === "\n") {
      currentRow.push(currentCell);
      rows.push(currentRow);
      currentCell = "";
      currentRow = [];
    } else if (char === "\r") {
      // Ignore CR. LF is handled separately.
    } else {
      currentCell += char;
    }
  }

  if (currentCell.length > 0 || currentRow.length > 0) {
    currentRow.push(currentCell);
    rows.push(currentRow);
  }

  return rows;
}

export function parseAttendanceCsv(csvText) {
  const rows = parseCsvRows(csvText);
  if (rows.length === 0) return [];

  const [headerRow, ...dataRows] = rows;
  const headerMap = ATTENDANCE_HEADERS.map((header) =>
    headerRow.findIndex((raw) => raw.trim() === header)
  );

  return dataRows
    .filter((rawRow) => rawRow.some((cell) => (cell || "").trim() !== ""))
    .map((rawRow) => {
      const row = {};
      ATTENDANCE_HEADERS.forEach((header, index) => {
        const sourceIndex = headerMap[index];
        row[header] = sourceIndex >= 0 ? rawRow[sourceIndex] || "" : "";
      });
      return row;
    });
}
