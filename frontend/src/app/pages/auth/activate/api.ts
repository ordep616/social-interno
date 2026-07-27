import { ClientConfig } from '../../../hooks/useClientConfig';
import { trimTrailingSlash } from '../../../utils/common';

export type ActivationRole = 'user' | 'group_admin';

export type ActivationValidationResponse = {
  target_user_id: string;
  username: string;
  role: ActivationRole;
  expires_at: string;
};

export type RegistrationResponse = {
  user_id: string;
};

export type ActivationErrorCode =
  | 'activation_not_found'
  | 'activation_unavailable'
  | 'activation_conflict'
  | 'invalid_request'
  | 'password_policy_violation'
  | 'rate_limited'
  | 'upstream_invalid_response'
  | 'service_unavailable'
  | 'access_denied'
  | 'unknown';

export class ActivationApiError extends Error {
  status: number;

  code: ActivationErrorCode;

  constructor(status: number, code: ActivationErrorCode, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export const activationBackendUrl = (clientConfig: ClientConfig): string =>
  trimTrailingSlash(clientConfig.backendUrl ?? 'http://127.0.0.1:8081');

const PUBLIC_ERROR_CODES = new Set<ActivationErrorCode>([
  'activation_not_found',
  'activation_unavailable',
  'activation_conflict',
  'invalid_request',
  'password_policy_violation',
  'rate_limited',
  'upstream_invalid_response',
  'service_unavailable',
  'access_denied',
]);

const USERNAME_REGEX = /^[a-z0-9][a-z0-9._-]{1,30}[a-z0-9]$/;

const isActivationErrorCode = (code: unknown): code is ActivationErrorCode =>
  typeof code === 'string' && PUBLIC_ERROR_CODES.has(code as ActivationErrorCode);

const activationErrorCodeFromStatus = (status: number): ActivationErrorCode => {
  if (status === 400) return 'invalid_request';
  if (status === 404) return 'activation_not_found';
  if (status === 409) return 'activation_conflict';
  if (status === 410) return 'activation_unavailable';
  if (status === 422) return 'password_policy_violation';
  if (status === 429) return 'rate_limited';
  if (status === 401 || status === 403) return 'access_denied';
  if (status === 502) return 'upstream_invalid_response';
  if (status === 503) return 'service_unavailable';
  return 'unknown';
};

const readPublicErrorCode = async (response: Response): Promise<ActivationErrorCode> => {
  try {
    const payload = await response.clone().json();
    if (typeof payload !== 'object' || payload === null) {
      return activationErrorCodeFromStatus(response.status);
    }

    const code = (payload as { error?: { code?: unknown } }).error?.code;
    if (isActivationErrorCode(code)) return code;
  } catch {
    return activationErrorCodeFromStatus(response.status);
  }

  return activationErrorCodeFromStatus(response.status);
};

const activationErrorMessage = (status: number): string =>
  `Requisicao de ativacao falhou (${status}).`;

const isActivationRole = (role: unknown): role is ActivationRole =>
  role === 'user' || role === 'group_admin';

const isActivationValidationResponse = (
  payload: unknown
): payload is ActivationValidationResponse => {
  if (typeof payload !== 'object' || payload === null) return false;
  const response = payload as Record<string, unknown>;

  return (
    typeof response.target_user_id === 'string' &&
    typeof response.username === 'string' &&
    USERNAME_REGEX.test(response.username) &&
    isActivationRole(response.role) &&
    typeof response.expires_at === 'string'
  );
};

const isRegistrationResponse = (payload: unknown): payload is RegistrationResponse => {
  if (typeof payload !== 'object' || payload === null) return false;
  const response = payload as Record<string, unknown>;

  return typeof response.user_id === 'string';
};

const readJson = async (response: Response): Promise<unknown> => {
  try {
    return await response.json();
  } catch {
    throw new ActivationApiError(
      502,
      'upstream_invalid_response',
      'Resposta de ativacao fora do contrato.'
    );
  }
};

const activationRequest = async (
  backendUrl: string,
  path: string,
  expectedStatus: number,
  body: object
): Promise<unknown> => {
  const response = await fetch(`${backendUrl}${path}`, {
    method: 'POST',
    cache: 'no-store',
    credentials: 'omit',
    referrerPolicy: 'no-referrer',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const code = await readPublicErrorCode(response);

    throw new ActivationApiError(response.status, code, activationErrorMessage(response.status));
  }

  if (response.status !== expectedStatus) {
    throw new ActivationApiError(
      502,
      'upstream_invalid_response',
      'Resposta de ativacao fora do contrato.'
    );
  }

  return readJson(response);
};

const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });

const mockActivation = async (token: string): Promise<ActivationValidationResponse | undefined> => {
  if (!import.meta.env.DEV || !token.startsWith('mock:')) return undefined;

  await sleep(250);

  const scenario = token.slice('mock:'.length);
  if (scenario === 'not-found') {
    throw new ActivationApiError(404, 'activation_not_found', activationErrorMessage(404));
  }
  if (scenario === 'expired' || scenario === 'used' || scenario === 'revoked') {
    throw new ActivationApiError(410, 'activation_unavailable', activationErrorMessage(410));
  }
  if (scenario === 'conflict') {
    throw new ActivationApiError(409, 'activation_conflict', activationErrorMessage(409));
  }
  if (scenario === 'rate-limit') {
    throw new ActivationApiError(429, 'rate_limited', activationErrorMessage(429));
  }
  if (scenario === 'unavailable') {
    throw new ActivationApiError(503, 'service_unavailable', activationErrorMessage(503));
  }
  if (scenario === 'network') {
    throw new TypeError('Failed to fetch');
  }

  return {
    target_user_id: scenario === 'group' ? '@coordenador:localhost' : '@pedro:localhost',
    username: scenario === 'group' ? 'coordenador' : 'pedro',
    role: scenario === 'group' ? 'group_admin' : 'user',
    expires_at: '2026-07-28T12:00:00Z',
  };
};

const mockRegistration = async (
  token: string,
  validation: ActivationValidationResponse
): Promise<RegistrationResponse | undefined> => {
  if (!import.meta.env.DEV || !token.startsWith('mock:')) return undefined;

  await sleep(250);

  const scenario = token.slice('mock:'.length);
  if (scenario === 'invalid-password') {
    throw new ActivationApiError(422, 'password_policy_violation', activationErrorMessage(422));
  }
  if (scenario === 'register-conflict') {
    throw new ActivationApiError(409, 'activation_conflict', activationErrorMessage(409));
  }
  if (scenario === 'register-rate-limit') {
    throw new ActivationApiError(429, 'rate_limited', activationErrorMessage(429));
  }
  if (scenario === 'register-unavailable') {
    throw new ActivationApiError(503, 'service_unavailable', activationErrorMessage(503));
  }
  if (scenario === 'register-network') {
    throw new TypeError('Failed to fetch');
  }

  return {
    user_id: validation.target_user_id,
  };
};

export const validateActivation = async (
  backendUrl: string,
  invitationToken: string
): Promise<ActivationValidationResponse> => {
  const mockResponse = await mockActivation(invitationToken);
  if (mockResponse) return mockResponse;

  const payload = await activationRequest(backendUrl, '/v1/activation-validations', 200, {
    invitation_token: invitationToken,
  });

  if (!isActivationValidationResponse(payload)) {
    throw new ActivationApiError(
      502,
      'upstream_invalid_response',
      'Resposta de ativacao fora do contrato.'
    );
  }

  return payload;
};

export const registerActivation = async (
  backendUrl: string,
  invitationToken: string,
  password: string,
  validation: ActivationValidationResponse
): Promise<RegistrationResponse> => {
  const mockResponse = await mockRegistration(invitationToken, validation);
  if (mockResponse) return mockResponse;

  const payload = await activationRequest(backendUrl, '/v1/registrations', 201, {
    invitation_token: invitationToken,
    password,
  });

  if (!isRegistrationResponse(payload)) {
    throw new ActivationApiError(
      502,
      'upstream_invalid_response',
      'Resposta de ativacao fora do contrato.'
    );
  }

  return payload;
};
