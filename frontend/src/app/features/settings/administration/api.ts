import { ClientConfig } from '../../../hooks/useClientConfig';
import { trimTrailingSlash } from '../../../utils/common';

export type AccountRole = 'user' | 'group_admin' | 'platform_admin';
export type CreatableAccountRole = Exclude<AccountRole, 'platform_admin'>;

export type AdminAccount = {
  user_id: string;
  display_name: string | null;
  role: AccountRole | null;
  admin: boolean;
  deactivated: boolean;
  locked: boolean;
  suspended: boolean;
};

export type AccountListResponse = {
  accounts: AdminAccount[];
  total: number;
  next_token: string | null;
};

export type CapabilitiesResponse = {
  user_id: string;
  role: AccountRole;
  capabilities: {
    can_manage_user_activations?: boolean;
    can_manage_accounts?: boolean;
  };
};

export type InvitationCreatedResponse = {
  id: string;
  role: CreatableAccountRole;
  status: string;
  created_by: string;
  target_user_id: string;
  created_at: string;
  expires_at: string;
  used_at: string | null;
  revoked_at: string | null;
  accepted_user_id: string | null;
  invite_url: string;
};

export class AdminApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const administrationBackendUrl = (clientConfig: ClientConfig): string =>
  trimTrailingSlash(clientConfig.backendUrl ?? 'http://127.0.0.1:8081');

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload: unknown = await response.json();
    if (
      typeof payload === 'object' &&
      payload &&
      'detail' in payload &&
      typeof payload.detail === 'string'
    ) {
      return payload.detail;
    }
  } catch {
    // ignore malformed error payload
  }
  return `Requisição administrativa falhou (${response.status}).`;
};

async function adminRequest<T>(
  backendUrl: string,
  accessToken: string,
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${backendUrl}${path}`, {
    ...init,
    headers: {
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      Authorization: `Bearer ${accessToken}`,
      ...init.headers,
    },
  });

  if (!response.ok) {
    throw new AdminApiError(response.status, await parseErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const getCurrentCapabilities = (
  backendUrl: string,
  accessToken: string
): Promise<CapabilitiesResponse> =>
  adminRequest<CapabilitiesResponse>(backendUrl, accessToken, '/v1/me/capabilities');

export const listAccounts = (
  backendUrl: string,
  accessToken: string
): Promise<AccountListResponse> =>
  adminRequest<AccountListResponse>(backendUrl, accessToken, '/v1/admin/accounts');

export const issueActivation = (
  backendUrl: string,
  accessToken: string,
  username: string,
  role: CreatableAccountRole
): Promise<InvitationCreatedResponse> =>
  adminRequest<InvitationCreatedResponse>(backendUrl, accessToken, '/v1/admin/invitations', {
    method: 'POST',
    body: JSON.stringify({ username, role }),
  });

export const updateAccount = (
  backendUrl: string,
  accessToken: string,
  userId: string,
  payload: { display_name?: string; locked?: boolean }
): Promise<AdminAccount> =>
  adminRequest<AdminAccount>(
    backendUrl,
    accessToken,
    `/v1/admin/accounts/${encodeURIComponent(userId)}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }
  );

export const resetAccountPassword = (
  backendUrl: string,
  accessToken: string,
  userId: string,
  newPassword: string
): Promise<void> =>
  adminRequest<void>(
    backendUrl,
    accessToken,
    `/v1/admin/accounts/${encodeURIComponent(userId)}/password-reset`,
    {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword, logout_devices: true }),
    }
  );

export const deactivateAccount = (
  backendUrl: string,
  accessToken: string,
  userId: string
): Promise<void> =>
  adminRequest<void>(
    backendUrl,
    accessToken,
    `/v1/admin/accounts/${encodeURIComponent(userId)}?erase=true`,
    {
      method: 'DELETE',
    }
  );
