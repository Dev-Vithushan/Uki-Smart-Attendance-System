import { list, put, del } from "@vercel/blob";

export async function listAllByPrefix(prefix) {
  let cursor;
  const blobs = [];

  do {
    const response = await list({
      prefix,
      limit: 1000,
      cursor,
    });

    blobs.push(...response.blobs);
    cursor = response.cursor;
  } while (cursor);

  return blobs;
}

export async function findBlobByPath(pathname) {
  const blobs = await listAllByPrefix(pathname);
  return blobs.find((blob) => blob.pathname === pathname) || null;
}

export async function getBlobText(pathname) {
  const blob = await findBlobByPath(pathname);
  if (!blob) return null;

  const response = await fetch(blob.url);
  if (!response.ok) {
    throw new Error(`Failed reading blob ${pathname}: ${response.status}`);
  }

  return response.text();
}

export async function getBlobJson(pathname) {
  const text = await getBlobText(pathname);
  if (text === null) return null;
  return JSON.parse(text);
}

export async function putBlobText(
  pathname,
  text,
  contentType = "text/plain; charset=utf-8"
) {
  const blob = await put(pathname, text, {
    access: "public",
    addRandomSuffix: false,
    allowOverwrite: true,
    contentType,
  });

  return blob;
}

export async function putBlobJson(pathname, value) {
  const body = JSON.stringify(value, null, 2);
  return putBlobText(pathname, body, "application/json; charset=utf-8");
}

export async function deleteBlobByPath(pathname) {
  const blob = await findBlobByPath(pathname);
  if (!blob) return false;

  await del(blob.url);
  return true;
}
