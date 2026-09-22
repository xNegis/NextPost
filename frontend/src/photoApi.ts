import { ApiError } from "./api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export interface ApplicationConfig {
  consultation_min_photos: number;
  consultation_max_photos: number;
  max_open_consultations: number;
  photo_max_input_bytes: number;
}

export interface UploadSession {
  id: string;
  lease_expires_at: string;
}

export interface UploadedImage {
  id: string;
  width: number;
  height: number;
}

function isApplicationConfig(value: unknown): value is ApplicationConfig {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.consultation_min_photos === "number" &&
    typeof record.consultation_max_photos === "number" &&
    typeof record.max_open_consultations === "number" &&
    typeof record.photo_max_input_bytes === "number"
  );
}

function isUploadSession(value: unknown): value is UploadSession {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" && typeof record.lease_expires_at === "string"
  );
}

function isUploadedImage(value: unknown): value is UploadedImage {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" &&
    typeof record.width === "number" &&
    typeof record.height === "number"
  );
}

function extractErrorCode(body: unknown): string | null {
  if (typeof body !== "object" || body === null) return null;
  const detail = (body as Record<string, unknown>).detail;
  if (typeof detail !== "object" || detail === null) return null;
  const code = (detail as Record<string, unknown>).code;
  return typeof code === "string" ? code : null;
}

function parseJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export async function fetchApplicationConfig(): Promise<ApplicationConfig> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/application-config`, {
      credentials: "include",
    });
  } catch {
    throw new ApiError("network");
  }

  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(extractErrorCode(body) ?? "unavailable");
  }
  if (!isApplicationConfig(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function createUploadSession(): Promise<UploadSession> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/photo-upload-sessions`, {
      method: "POST",
      credentials: "include",
    });
  } catch {
    throw new ApiError("network");
  }

  const body: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (!response.ok) {
    throw new ApiError(extractErrorCode(body) ?? "unavailable");
  }
  if (!isUploadSession(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function renewUploadSession(
  sessionId: string,
): Promise<UploadSession> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/photo-upload-sessions/${sessionId}/lease`,
      { method: "POST", credentials: "include" },
    );
  } catch {
    throw new ApiError("network");
  }

  const body: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (!response.ok) {
    throw new ApiError(extractErrorCode(body) ?? "unavailable");
  }
  if (!isUploadSession(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export function uploadImage(
  sessionId: string,
  file: File,
  attemptId: string,
  onProgress: (fraction: number) => void,
  onBytesSent: () => void,
): Promise<UploadedImage> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open(
      "POST",
      `${API_BASE_URL}/api/photo-upload-sessions/${sessionId}/images`,
    );
    request.withCredentials = true;

    request.upload.onprogress = (event) => {
      if (event.lengthComputable && event.total > 0) {
        onProgress(event.loaded / event.total);
      }
    };
    request.upload.onload = () => {
      onBytesSent();
    };
    request.onload = () => {
      const body: unknown = parseJson(request.responseText);
      if (request.status === 401) {
        reject(new ApiError("unauthenticated"));
        return;
      }
      if (
        request.status >= 200 &&
        request.status < 300 &&
        isUploadedImage(body)
      ) {
        resolve(body);
        return;
      }
      reject(new ApiError(extractErrorCode(body) ?? "unavailable"));
    };
    request.onerror = () => reject(new ApiError("network"));
    request.onabort = () => reject(new ApiError("network"));

    const form = new FormData();
    form.append("file", file);
    form.append("attempt_id", attemptId);
    request.send(form);
  });
}

export async function removeImage(
  sessionId: string,
  imageId: string,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/photo-upload-sessions/${sessionId}/images/${imageId}`,
      { method: "DELETE", credentials: "include" },
    );
  } catch {
    throw new ApiError("network");
  }

  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (!response.ok) {
    throw new ApiError("unavailable");
  }
}

export async function discardUploadSession(sessionId: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/photo-upload-sessions/${sessionId}`,
      { method: "DELETE", credentials: "include", keepalive: true },
    );
  } catch {
    throw new ApiError("network");
  }

  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (!response.ok) {
    throw new ApiError("unavailable");
  }
}

export async function fetchImageUrl(
  sessionId: string,
  imageId: string,
): Promise<string> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/photo-upload-sessions/${sessionId}/images/${imageId}/content`,
      { credentials: "include" },
    );
  } catch {
    throw new ApiError("network");
  }

  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (!response.ok) {
    throw new ApiError("unavailable");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
