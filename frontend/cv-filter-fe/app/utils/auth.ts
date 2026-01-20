/**
 * Authentication utilities for token management
 */

type RefreshResponse = {
  access?: string;
  detail?: string;
};

/**
 * Attempts to refresh the access token using the stored refresh token
 * @returns The new access token if successful, null otherwise
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken =
    sessionStorage.getItem("refresh") || localStorage.getItem("refresh_token");

  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch("/api/auth/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!response.ok) {
      // Refresh token is invalid or expired
      clearAuthTokens();
      return null;
    }

    const body = (await response.json()) as RefreshResponse;
    if (body.access) {
      // Store the new access token
      console.log("✅ Token refreshed successfully");
      sessionStorage.setItem("access", body.access);
      localStorage.setItem("access_token", body.access);
      return body.access;
    }

    return null;
  } catch (error) {
    console.error("❌ Token refresh error:", error);
    return null;
  }
}

/**
 * Makes an authenticated API request with automatic token refresh on 401
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const getAccessToken = () =>
    sessionStorage.getItem("access") || localStorage.getItem("access_token");

  let accessToken = getAccessToken();

  if (!accessToken) {
    throw new Error("No access token available");
  }

  // Add authorization header
  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${accessToken}`);

  // Make the first request
  let response = await fetch(url, {
    ...options,
    headers,
  });

  // If we get a 401, try to refresh the token once
  if (response.status === 401) {
    console.log("🔄 Token expired, refreshing...");
    const newToken = await refreshAccessToken();

    if (newToken) {
      // Retry the request with the new token
      headers.set("Authorization", `Bearer ${newToken}`);
      response = await fetch(url, {
        ...options,
        headers,
      });
    } else {
      console.warn("⚠️ Token refresh failed, please sign in again");
    }
  }

  return response;
}

/**
 * Clears all authentication tokens from storage
 */
export function clearAuthTokens(): void {
  sessionStorage.removeItem("access");
  sessionStorage.removeItem("refresh");
  sessionStorage.removeItem("user");
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

/**
 * Checks if user is authenticated (has valid tokens)
 */
export function isAuthenticated(): boolean {
  const accessToken =
    sessionStorage.getItem("access") || localStorage.getItem("access_token");
  return !!accessToken;
}
