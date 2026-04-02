import crypto from "node:crypto";
import { MASTER_FILE_PATH, STUDENT_IMAGES_PREFIX } from "./constants.js";
import {
  getBlobJson,
  putBlobJson,
  putBlobText,
  deleteBlobByPath,
} from "./blobStore.js";

export function normalizeStudentName(name) {
  const trimmed = String(name || "").trim().replace(/\s+/g, " ");
  if (!trimmed) return "";

  return trimmed
    .split(" ")
    .map((part) => {
      const lower = part.toLowerCase();
      return lower.charAt(0).toUpperCase() + lower.slice(1);
    })
    .join(" ");
}

function validateName(name) {
  if (!name) {
    return "Name is required.";
  }
  if (name.length < 2) {
    return "Name must be at least 2 characters.";
  }
  if (name.includes(",")) {
    return "Commas are not allowed in names.";
  }
  return null;
}

function getStudentPublicShape(student) {
  return {
    id: student.id,
    name: student.name,
    imageUrl: student.imageUrl,
    descriptor: student.descriptor,
    registeredAt: student.registeredAt,
  };
}

function parseImageDataUrl(imageDataUrl) {
  const dataUrl = String(imageDataUrl || "");
  const match = dataUrl.match(/^data:(image\/[a-zA-Z0-9+.-]+);base64,(.+)$/);
  if (!match) {
    throw new Error("Invalid image payload.");
  }

  const contentType = match[1];
  const base64Data = match[2];
  const buffer = Buffer.from(base64Data, "base64");
  if (buffer.length === 0) {
    throw new Error("Empty image payload.");
  }

  return { contentType, buffer };
}

export async function getMasterStudents() {
  const data = await getBlobJson(MASTER_FILE_PATH);
  if (!Array.isArray(data)) return [];
  return data;
}

async function saveMasterStudents(students) {
  const sorted = [...students].sort((a, b) => a.name.localeCompare(b.name));
  await putBlobJson(MASTER_FILE_PATH, sorted);
  return sorted;
}

export function findStudentByName(students, name) {
  const normalized = normalizeStudentName(name).toLowerCase();
  return students.find((student) => student.name.toLowerCase() === normalized);
}

export async function listStudents() {
  const students = await getMasterStudents();
  return students.map(getStudentPublicShape);
}

export async function registerStudent({ name, imageDataUrl, descriptor }) {
  const normalizedName = normalizeStudentName(name);
  const nameError = validateName(normalizedName);
  if (nameError) {
    return { success: false, message: nameError };
  }

  if (!Array.isArray(descriptor) || descriptor.length < 16) {
    return { success: false, message: "Face descriptor is missing or invalid." };
  }

  const numericDescriptor = descriptor.map((value) => Number(value));
  if (numericDescriptor.some((value) => Number.isNaN(value))) {
    return { success: false, message: "Face descriptor contains invalid numbers." };
  }

  let imagePayload;
  try {
    imagePayload = parseImageDataUrl(imageDataUrl);
  } catch (error) {
    return { success: false, message: error.message };
  }

  const students = await getMasterStudents();
  if (findStudentByName(students, normalizedName)) {
    return { success: false, message: `Student "${normalizedName}" already exists.` };
  }

  const id = crypto.randomUUID();
  const imagePath = `${STUDENT_IMAGES_PREFIX}${id}.jpg`;
  const imageUpload = await putBlobText(imagePath, imagePayload.buffer, imagePayload.contentType);

  const student = {
    id,
    name: normalizedName,
    descriptor: numericDescriptor,
    imagePath,
    imageUrl: imageUpload.url,
    registeredAt: new Date().toISOString(),
  };

  const updated = await saveMasterStudents([...students, student]);
  return {
    success: true,
    message: `Student ${normalizedName} registered successfully.`,
    student: getStudentPublicShape(student),
    totalRegistered: updated.length,
  };
}

export async function renameStudent(oldName, newName) {
  const normalizedOld = normalizeStudentName(oldName);
  const normalizedNew = normalizeStudentName(newName);
  const nameError = validateName(normalizedNew);
  if (nameError) {
    return { success: false, message: nameError };
  }

  const students = await getMasterStudents();
  const existing = findStudentByName(students, normalizedOld);
  if (!existing) {
    return { success: false, message: `Student "${normalizedOld}" not found.` };
  }

  const duplicate = findStudentByName(students, normalizedNew);
  if (duplicate && duplicate.id !== existing.id) {
    return { success: false, message: `Student "${normalizedNew}" already exists.` };
  }

  const updatedStudents = students.map((student) =>
    student.id === existing.id
      ? {
          ...student,
          name: normalizedNew,
        }
      : student
  );

  const saved = await saveMasterStudents(updatedStudents);
  return {
    success: true,
    message: `Student renamed to ${normalizedNew}.`,
    students: saved.map(getStudentPublicShape),
  };
}

export async function deleteStudent(name) {
  const normalizedName = normalizeStudentName(name);
  const students = await getMasterStudents();
  const target = findStudentByName(students, normalizedName);

  if (!target) {
    return { success: false, message: `Student "${normalizedName}" not found.` };
  }

  const updatedStudents = students.filter((student) => student.id !== target.id);
  const saved = await saveMasterStudents(updatedStudents);

  if (target.imagePath) {
    try {
      await deleteBlobByPath(target.imagePath);
    } catch (_error) {
      // Ignore orphan image cleanup errors.
    }
  }

  return {
    success: true,
    message: `Student "${target.name}" deleted successfully.`,
    students: saved.map(getStudentPublicShape),
  };
}
