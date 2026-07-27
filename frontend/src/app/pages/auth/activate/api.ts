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
  | 'token_not_found'
  | 'token_unavailable'
  | 'identity_unavailable'
  | 'rate_limited'
  | 'invalid_password'
  | 'access_denied'
  | 'backend_unavailable'
  | 'invalid_response'
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

const activationErrorCode = (status: number): ActivationErrorCode => {
  if (status === 404) return 'token_not_found';
  if (status === 410) return 'token_unavailable';
  if (status === 409) return 'identity_unavailable';
  if (status === 429) return 'rate_limited';
  if (status === 422) return 'invalid_password';
  if (status === 401 || status === 403) return 'access_denied';
  if (status === 502) return 'invalid_response';
  if (status === 503) return 'backend_unavailable';
  return 'unknown';
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
    throw new ActivationApiError(502, 'invalid_response', 'Resposta de ativacao fora do contrato.');
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
    throw new ActivationApiError(
      response.status,
      activationErrorCode(response.status),
      activationErrorMessage(response.status)
    );
  }

  if (response.status !== expectedStatus) {
    throw new ActivationApiError(502, 'invalid_response', 'Resposta de ativacao fora do contrato.');
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
    throw new ActivationApiError(404, 'token_not_found', activationErrorMessage(404));
  }
  if (scenario === 'expired' || scenario === 'used' || scenario === 'revoked') {
    throw new ActivationApiError(410, 'token_unavailable', activationErrorMessage(410));
  }
  if (scenario === 'conflict') {
    throw new ActivationApiError(409, 'identity_unavailable', activationErrorMessage(409));
  }
  if (scenario === 'rate-limit') {
    throw new ActivationApiError(429, 'rate_limited', activationErrorMessage(429));
  }
  if (scenario === 'unavailable') {
    throw new ActivationApiError(503, 'backend_unavailable', activationErrorMessage(503));
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
    throw new ActivationApiError(422, 'invalid_password', activationErrorMessage(422));
  }
  if (scenario === 'register-conflict') {
    throw new ActivationApiError(409, 'identity_unavailable', activationErrorMessage(409));
  }
  if (scenario === 'register-rate-limit') {
    throw new ActivationApiError(429, 'rate_limited', activationErrorMessage(429));
  }
  if (scenario === 'register-unavailable') {
    throw new ActivationApiError(503, 'backend_unavailable', activationErrorMessage(503));
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
    throw new ActivationApiError(502, 'invalid_response', 'Resposta de ativacao fora do contrato.');
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
    throw new ActivationApiError(502, 'invalid_response', 'Resposta de ativacao fora do contrato.');
  }

  return payload;
};
