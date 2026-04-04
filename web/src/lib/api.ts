/**
 * Returns the API base URL with no trailing slash.
 *
 * NEXT_PUBLIC_API_URL may be set to a bare origin (e.g. "https://api.example.com")
 * or already include the "/api/v1" path prefix — both forms are accepted.
 * When the variable is unset the function defaults to "http://localhost:8000/api/v1".
 */
export const getApiBase = (): string => {
  const configuredBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const normalizedBase = configuredBase.replace(/\/+$/, "");
  return normalizedBase.endsWith("/api/v1")
    ? normalizedBase
    : `${normalizedBase}/api/v1`;
};
