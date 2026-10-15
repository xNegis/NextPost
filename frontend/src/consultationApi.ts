import { ApiError } from "./api";
import { isAudience, type Audience } from "./audience";
import { privateLinkHeaders } from "./consultationLink";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

const UUID_RE =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

const CURSOR_MAX_LENGTH = 512;
const CURSOR_RE = /^[A-Za-z0-9_-]+$/;

function isUuid(value: unknown): value is string {
  return typeof value === "string" && UUID_RE.test(value);
}

function hasExactKeys(
  record: Record<string, unknown>,
  expected: string[],
): boolean {
  const keys = Object.keys(record);
  if (keys.length !== expected.length) return false;
  return expected.every((key) => key in record);
}

function isValidPublishedAt(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const match =
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?(?:Z|\+00:00)$/.exec(
      value,
    );
  if (!match) return false;
  const date = new Date(value);
  return (
    Number(match[1]) === date.getUTCFullYear() &&
    Number(match[2]) === date.getUTCMonth() + 1 &&
    Number(match[3]) === date.getUTCDate() &&
    Number(match[4]) === date.getUTCHours() &&
    Number(match[5]) === date.getUTCMinutes() &&
    Number(match[6]) === date.getUTCSeconds()
  );
}

function isValidCursor(value: unknown): value is string | null {
  if (value === null) return true;
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= CURSOR_MAX_LENGTH &&
    CURSOR_RE.test(value)
  );
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value > 0;
}

export interface ConsultationPublished {
  id: string;
  state: "open";
  audience: string;
}

export interface ConsultationCapacity {
  open_count: number;
  limit: number;
  can_start: boolean;
}

export interface ConsultationPhoto {
  id: string;
  width: number;
  height: number;
}

export interface ConsultationDetail {
  id: string;
  owner_nickname: string;
  question: string;
  context: string | null;
  audience: string;
  state: "open";
  published_at: string;
  photos: ConsultationPhoto[];
}

export interface OwnerLink {
  active: boolean;
  generation: string;
  token: string | null;
}

export type MyConsultationState = "open" | "finalized";

export interface MyConsultationOpenListItem {
  id: string;
  state: "open";
  question: string;
  audience: Audience;
  published_at: string;
}

export interface MyConsultationFinalizedListItem {
  id: string;
  state: "finalized";
  published_at: string;
}

export type MyConsultationListItem =
  MyConsultationOpenListItem | MyConsultationFinalizedListItem;

export interface MyConsultationList {
  items: MyConsultationListItem[];
  next_cursor: string | null;
}

export interface MyConsultationOpenDetail {
  id: string;
  state: "open";
  owner_nickname: string;
  question: string;
  context: string | null;
  audience: Audience;
  published_at: string;
  photos: ConsultationPhoto[];
}

export interface MyConsultationFinalizedDetail {
  id: string;
  state: "finalized";
  published_at: string;
}

export type MyConsultationOwnerDetail =
  MyConsultationOpenDetail | MyConsultationFinalizedDetail;

export interface FeedPhoto {
  id: string;
  width: number;
  height: number;
}

export interface FeedItem {
  id: string;
  owner_nickname: string;
  question: string;
  context_excerpt: string | null;
  audience: "public";
  state: "open";
  published_at: string;
  is_owner: boolean;
  first_photo: FeedPhoto;
}

export interface Feed {
  items: FeedItem[];
  next_cursor: string | null;
}

function extractErrorCode(body: unknown): string | null {
  if (typeof body !== "object" || body === null) return null;
  const detail = (body as Record<string, unknown>).detail;
  if (typeof detail !== "object" || detail === null) return null;
  const code = (detail as Record<string, unknown>).code;
  return typeof code === "string" ? code : null;
}

function extractFieldErrors(body: unknown): Record<string, string> {
  if (typeof body !== "object" || body === null) return {};
  const detail = (body as Record<string, unknown>).detail;
  if (typeof detail !== "object" || detail === null) return {};
  const fieldErrors = (detail as Record<string, unknown>).field_errors;
  if (typeof fieldErrors !== "object" || fieldErrors === null) return {};
  const result: Record<string, string> = {};
  for (const [key, value] of Object.entries(fieldErrors)) {
    if (typeof value === "string") result[key] = value;
  }
  return result;
}

function isConsultationPublished(
  value: unknown,
): value is ConsultationPublished {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" &&
    record.state === "open" &&
    typeof record.audience === "string"
  );
}

function isConsultationCapacity(value: unknown): value is ConsultationCapacity {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.open_count === "number" &&
    typeof record.limit === "number" &&
    typeof record.can_start === "boolean"
  );
}

function isConsultationPhoto(value: unknown): value is ConsultationPhoto {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" &&
    isPositiveInteger(record.width) &&
    isPositiveInteger(record.height)
  );
}

function isConsultationDetail(value: unknown): value is ConsultationDetail {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (
    !hasExactKeys(record, [
      "id",
      "owner_nickname",
      "question",
      "context",
      "audience",
      "state",
      "published_at",
      "photos",
    ])
  ) {
    return false;
  }
  if (
    !isUuid(record.id) ||
    typeof record.owner_nickname !== "string" ||
    typeof record.question !== "string" ||
    !isAudience(record.audience) ||
    record.state !== "open" ||
    !isValidPublishedAt(record.published_at)
  ) {
    return false;
  }
  if (record.context !== null && typeof record.context !== "string")
    return false;
  if (!Array.isArray(record.photos) || !record.photos.every(isStrictPhoto))
    return false;
  const photoIds = record.photos.map((photo) => photo.id);
  return new Set(photoIds).size === photoIds.length;
}

function isStrictPhoto(value: unknown): value is ConsultationPhoto {
  if (!isConsultationPhoto(value)) return false;
  return (
    isUuid(value.id) &&
    hasExactKeys(value as unknown as Record<string, unknown>, [
      "id",
      "width",
      "height",
    ])
  );
}

function isOwnerLink(value: unknown): value is OwnerLink {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (typeof record.active !== "boolean") return false;
  if (typeof record.generation !== "string") return false;
  return record.token === null || typeof record.token === "string";
}

const OPEN_LIST_ITEM_KEYS = [
  "id",
  "state",
  "question",
  "audience",
  "published_at",
];
const FINALIZED_LIST_ITEM_KEYS = ["id", "state", "published_at"];
const OPEN_DETAIL_KEYS = [
  "id",
  "state",
  "owner_nickname",
  "question",
  "context",
  "audience",
  "published_at",
  "photos",
];
const FINALIZED_DETAIL_KEYS = ["id", "state", "published_at"];

function isMyConsultationOpenListItem(
  value: unknown,
): value is MyConsultationOpenListItem {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, OPEN_LIST_ITEM_KEYS)) return false;
  return (
    isUuid(record.id) &&
    record.state === "open" &&
    typeof record.question === "string" &&
    isAudience(record.audience) &&
    isValidPublishedAt(record.published_at)
  );
}

function isMyConsultationFinalizedListItem(
  value: unknown,
): value is MyConsultationFinalizedListItem {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, FINALIZED_LIST_ITEM_KEYS)) return false;
  return (
    isUuid(record.id) &&
    record.state === "finalized" &&
    isValidPublishedAt(record.published_at)
  );
}

function isMyConsultationListItem(
  value: unknown,
  state: MyConsultationState,
): value is MyConsultationListItem {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (record.state !== state) return false;
  if (state === "open") return isMyConsultationOpenListItem(value);
  return isMyConsultationFinalizedListItem(value);
}

function isMyConsultationList(
  value: unknown,
  state: MyConsultationState,
  limit: number,
): value is MyConsultationList {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, ["items", "next_cursor"])) return false;
  if (!Array.isArray(record.items)) return false;
  if (record.items.length > limit) return false;
  if (!isValidCursor(record.next_cursor)) return false;
  return record.items.every((item) => isMyConsultationListItem(item, state));
}

function isMyConsultationOpenDetail(
  value: unknown,
): value is MyConsultationOpenDetail {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, OPEN_DETAIL_KEYS)) return false;
  if (
    !isUuid(record.id) ||
    typeof record.owner_nickname !== "string" ||
    typeof record.question !== "string" ||
    !isAudience(record.audience) ||
    record.state !== "open" ||
    !isValidPublishedAt(record.published_at)
  ) {
    return false;
  }
  if (record.context !== null && typeof record.context !== "string")
    return false;
  return Array.isArray(record.photos) && record.photos.every(isStrictPhoto);
}

function isMyConsultationFinalizedDetail(
  value: unknown,
): value is MyConsultationFinalizedDetail {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, FINALIZED_DETAIL_KEYS)) return false;
  return (
    isUuid(record.id) &&
    record.state === "finalized" &&
    isValidPublishedAt(record.published_at)
  );
}

function isMyConsultationOwnerDetail(
  value: unknown,
): value is MyConsultationOwnerDetail {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (record.state === "open") return isMyConsultationOpenDetail(value);
  if (record.state === "finalized")
    return isMyConsultationFinalizedDetail(value);
  return false;
}

const FEED_ITEM_KEYS = [
  "id",
  "owner_nickname",
  "question",
  "context_excerpt",
  "audience",
  "state",
  "published_at",
  "is_owner",
  "first_photo",
];
const FEED_PHOTO_KEYS = ["id", "width", "height"];

function isFeedPhoto(value: unknown): value is FeedPhoto {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, FEED_PHOTO_KEYS)) return false;
  return (
    isUuid(record.id) &&
    isPositiveInteger(record.width) &&
    isPositiveInteger(record.height)
  );
}

function isFeedItem(value: unknown): value is FeedItem {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, FEED_ITEM_KEYS)) return false;
  return (
    isUuid(record.id) &&
    typeof record.owner_nickname === "string" &&
    typeof record.question === "string" &&
    (record.context_excerpt === null ||
      typeof record.context_excerpt === "string") &&
    record.audience === "public" &&
    record.state === "open" &&
    isValidPublishedAt(record.published_at) &&
    typeof record.is_owner === "boolean" &&
    isFeedPhoto(record.first_photo)
  );
}

function isFeed(value: unknown, limit: number): value is Feed {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (!hasExactKeys(record, ["items", "next_cursor"])) return false;
  if (!Array.isArray(record.items)) return false;
  if (record.items.length > limit) return false;
  if (!isValidCursor(record.next_cursor)) return false;
  return record.items.every(isFeedItem);
}

function requestOptions(token: string | null): RequestInit {
  return { credentials: "include", headers: privateLinkHeaders(token) };
}

export async function publishConsultation(
  sessionId: string,
  orderedImageIds: string[],
  question: string,
  context: string | null,
  audience: Audience,
): Promise<ConsultationPublished> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/consultations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        session_id: sessionId,
        ordered_image_ids: orderedImageIds,
        question,
        context,
        audience,
      }),
    });
  } catch {
    throw new ApiError("network");
  }

  const body: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (response.status === 422) {
    throw new ApiError("validation_error", extractFieldErrors(body));
  }
  if (!response.ok) {
    throw new ApiError(extractErrorCode(body) ?? "unavailable");
  }
  if (!isConsultationPublished(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function fetchConsultationCapacity(): Promise<ConsultationCapacity> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/consultation-capacity`, {
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
  if (!isConsultationCapacity(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function fetchConsultationDetail(
  consultationId: string,
  token: string | null = null,
): Promise<ConsultationDetail> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/consultations/${consultationId}`,
      requestOptions(token),
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
  if (!isConsultationDetail(body) || body.id !== consultationId) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function fetchFeed(
  limit = 20,
  cursor: string | null = null,
): Promise<Feed> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor !== null) params.set("cursor", cursor);

  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/consultations/feed?${params.toString()}`,
      { credentials: "include" },
    );
  } catch {
    throw new ApiError("network");
  }

  const body: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (response.status === 422) {
    throw new ApiError("validation_error", extractFieldErrors(body));
  }
  if (!response.ok) {
    throw new ApiError(extractErrorCode(body) ?? "unavailable");
  }
  if (!isFeed(body, limit)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function fetchConsultationPhotoUrl(
  consultationId: string,
  photoId: string,
  token: string | null = null,
): Promise<string> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/consultations/${consultationId}/photos/${photoId}/content`,
      requestOptions(token),
    );
  } catch {
    throw new ApiError("network");
  }

  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    throw new ApiError(extractErrorCode(body) ?? "unavailable");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export async function fetchMyConsultations(
  state: MyConsultationState,
  limit = 20,
  cursor: string | null = null,
): Promise<MyConsultationList> {
  const params = new URLSearchParams({ state, limit: String(limit) });
  if (cursor !== null) params.set("cursor", cursor);

  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/my-consultations?${params.toString()}`,
      { credentials: "include" },
    );
  } catch {
    throw new ApiError("network");
  }

  const body: unknown = await response.json().catch(() => null);
  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (response.status === 422) {
    throw new ApiError("validation_error", extractFieldErrors(body));
  }
  if (!response.ok) {
    throw new ApiError(extractErrorCode(body) ?? "unavailable");
  }
  if (!isMyConsultationList(body, state, limit)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function fetchMyConsultation(
  consultationId: string,
): Promise<MyConsultationOwnerDetail> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/my-consultations/${consultationId}`,
      { credentials: "include" },
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
  if (!isMyConsultationOwnerDetail(body) || body.id !== consultationId) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function fetchOwnerLink(
  consultationId: string,
): Promise<OwnerLink> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/consultations/${consultationId}/private-link`,
      { credentials: "include" },
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
  if (!isOwnerLink(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

async function mutateOwnerLink(
  consultationId: string,
  operation: string,
  expectedGeneration: string,
): Promise<OwnerLink> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/consultations/${consultationId}/private-link/${operation}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ expected_generation: expectedGeneration }),
      },
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
  if (!isOwnerLink(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export function disableOwnerLink(
  consultationId: string,
  expectedGeneration: string,
): Promise<OwnerLink> {
  return mutateOwnerLink(consultationId, "disable", expectedGeneration);
}

export function replaceOwnerLink(
  consultationId: string,
  expectedGeneration: string,
): Promise<OwnerLink> {
  return mutateOwnerLink(consultationId, "replace", expectedGeneration);
}

export function createOwnerLink(
  consultationId: string,
  expectedGeneration: string,
): Promise<OwnerLink> {
  return mutateOwnerLink(consultationId, "create", expectedGeneration);
}
