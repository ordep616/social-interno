import { createClient, type MatrixClient } from "matrix-js-sdk";

import { getMatrixHomeserverUrl } from "./config";
import type { MatrixSession } from "./types";

export function createMatrixClient(session: MatrixSession): MatrixClient {
  return createClient({
    baseUrl: getMatrixHomeserverUrl(),
    accessToken: session.accessToken,
    userId: session.userId,
    deviceId: session.deviceId,
  });
}
