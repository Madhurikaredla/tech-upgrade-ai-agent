import { getAuthToken } from "./authToken";

interface RoleObject {
  name: string;
  role_name: string;
  role_key: string;
  priority: number;
}

export interface UserInfo {
  userId: string;
  name: string;
  initials: string;
  /** Internal role keys, e.g. ["ROLE_ADMIN"] — keep internal, don't display raw */
  roles: string[];
  /** Human-readable role label for display, e.g. "Admin" */
  displayRole: string;
  phone?: string;
}

function computeInitials(name: string): string {
  return (
    name
      .split(/\s+/)
      .filter(Boolean)
      .map((p) => p[0].toUpperCase())
      .slice(0, 2)
      .join("") || "AU"
  );
}

export function decodePayload(token: string): Record<string, unknown> | null {
  try {
    // JWT uses base64url (- and _ instead of + and /); atob() needs standard base64.
    const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(b64));
  } catch {
    return null;
  }
}

function parseRoles(rolesRaw: unknown): { roles: string[]; displayRole: string } {
  if (!rolesRaw) return { roles: [], displayRole: "User" };

  // Array of role objects: [{name, role_name, role_key, priority}]
  if (Array.isArray(rolesRaw) && rolesRaw.length > 0) {
    const first = rolesRaw[0];
    if (first && typeof first === "object" && "role_key" in first) {
      const objs = rolesRaw as RoleObject[];
      const roles = objs.map((r) => r.role_key);
      // Highest access = lowest priority number
      const sorted = [...objs].sort((a, b) => a.priority - b.priority);
      const displayRole = sorted[0]?.role_name ?? "User";
      return { roles, displayRole };
    }
    // Array of plain strings
    const roles = rolesRaw.map(String);
    return { roles, displayRole: roles[0] ?? "User" };
  }

  // Single string
  if (typeof rolesRaw === "string") {
    return { roles: [rolesRaw], displayRole: rolesRaw };
  }

  return { roles: [], displayRole: "User" };
}

export function getUserInfo(): UserInfo {
  try {
    const token = getAuthToken();
    if (!token) return _fallback();
    const payload = decodePayload(token);
    if (!payload) return _fallback();

    const userId = String(payload.userId ?? payload.sub ?? payload.id ?? "guest");

    const rawName =
      payload.name ?? payload.fullName ?? payload.firstName ?? payload.username;
    const name =
      rawName &&
      String(rawName) !== "undefined" &&
      String(rawName) !== "null"
        ? String(rawName)
        : "Admin User";

    const { roles, displayRole } = parseRoles(
      payload.roles ?? payload.role ?? payload.authorities
    );

    const phone = payload.phone ? String(payload.phone) : undefined;

    return { userId, name, initials: computeInitials(name), roles, displayRole, phone };
  } catch {
    return _fallback();
  }
}

function _fallback(): UserInfo {
  return { userId: "guest", name: "Admin User", initials: "AU", roles: [], displayRole: "User" };
}

export function isAdmin(info?: UserInfo): boolean {
  const { roles } = info ?? getUserInfo();
  return roles.includes("ROLE_ADMIN");
}

/** Returns the primary role key from the stored token (used as the active-role header). */
export function getActiveRole(): string {
  try {
    const token = getAuthToken();
    if (!token) return "";
    const payload = decodePayload(token);
    if (!payload) return "";
    const rolesRaw = payload.roles ?? payload.role ?? payload.authorities;
    if (!rolesRaw) return "";
    if (Array.isArray(rolesRaw) && rolesRaw.length > 0) {
      const first = rolesRaw[0];
      if (first && typeof first === "object" && "role_key" in first) {
        const sorted = [...(rolesRaw as RoleObject[])].sort((a, b) => a.priority - b.priority);
        return sorted[0]?.role_key ?? "";
      }
      return String(rolesRaw[0]);
    }
    if (typeof rolesRaw === "string") return rolesRaw;
    return "";
  } catch {
    return "";
  }
}

export function avatarColor(name: string): string {
  const palette = [
    "#7B78CC", "#9B78CC", "#5AAED0", "#4AAD89",
    "#C49040", "#C87070", "#D47AAF", "#4FA8C2",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return palette[Math.abs(hash) % palette.length];
}
