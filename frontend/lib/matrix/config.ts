const DEFAULT_LOCAL_HOMESERVER = "http://localhost:8008";

export function getMatrixHomeserverUrl(): string {
  const configured = process.env.NEXT_PUBLIC_MATRIX_HOMESERVER_URL?.trim();
  return configured || DEFAULT_LOCAL_HOMESERVER;
}
