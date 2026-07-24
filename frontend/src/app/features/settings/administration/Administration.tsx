import React, {
  ChangeEventHandler,
  FormEventHandler,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { Box, Button, Chip, Icon, IconButton, Icons, Input, Scroll, Spinner, Text } from 'folds';
import { Page, PageContent, PageHeader } from '../../../components/page';
import { SequenceCard } from '../../../components/sequence-card';
import { SettingTile } from '../../../components/setting-tile';
import { BreakWord } from '../../../styles/Text.css';
import { SequenceCardStyle } from '../styles.css';
import { useMatrixClient } from '../../../hooks/useMatrixClient';
import { useClientConfig } from '../../../hooks/useClientConfig';
import {
  AccountRole,
  AdminAccount,
  CreatableAccountRole,
  administrationBackendUrl,
  deactivateAccount,
  issueActivation,
  listAccounts,
  resetAccountPassword,
  updateAccount,
} from './api';

const ROLE_LABEL: Record<AccountRole | 'none', string> = {
  user: 'Usuário',
  group_admin: 'Admin de grupo',
  platform_admin: 'Administração da plataforma',
  none: 'Sem papel corporativo',
};

const accountDisplayName = (account: AdminAccount): string =>
  account.display_name || account.user_id;

const accountStatus = (account: AdminAccount): string => {
  if (account.deactivated) return 'Desativada';
  if (account.locked || account.suspended) return 'Bloqueada';
  return 'Ativa';
};

const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) return error.message;
  return 'Operação administrativa falhou.';
};

type RoleButtonProps = {
  accountRole: CreatableAccountRole;
  selected: boolean;
  disabled: boolean;
  onSelect: (accountRole: CreatableAccountRole) => void;
};
function RoleButton({ accountRole, selected, disabled, onSelect }: RoleButtonProps) {
  return (
    <Button
      type="button"
      size="300"
      radii="300"
      variant={selected ? 'Primary' : 'Secondary'}
      fill={selected ? 'Solid' : 'Soft'}
      outlined={!selected}
      aria-pressed={selected}
      disabled={disabled}
      onClick={() => onSelect(accountRole)}
    >
      <Text size="B300">{ROLE_LABEL[accountRole]}</Text>
    </Button>
  );
}

type AccountStatusChipProps = {
  account: AdminAccount;
};
function AccountStatusChip({ account }: AccountStatusChipProps) {
  return (
    <Box gap="100" wrap="Wrap">
      <Chip as="span" variant="Secondary" fill="Soft" radii="Pill">
        <Text size="B300">{accountStatus(account)}</Text>
      </Chip>
      {account.role && (
        <Chip as="span" variant="Secondary" fill="Soft" radii="Pill">
          <Text size="B300">{ROLE_LABEL[account.role]}</Text>
        </Chip>
      )}
    </Box>
  );
}

type AccountRowProps = {
  account: AdminAccount;
  selected: boolean;
  disabled: boolean;
  onEdit: (account: AdminAccount) => void;
  onPasswordReset: (account: AdminAccount) => void;
  onToggleLocked: (account: AdminAccount) => void;
  onDelete: (account: AdminAccount) => void;
};
function AccountRow({
  account,
  selected,
  disabled,
  onEdit,
  onPasswordReset,
  onToggleLocked,
  onDelete,
}: AccountRowProps) {
  const { deactivated, locked, suspended } = account;
  const blocked = locked || suspended;

  return (
    <SequenceCard
      className={SequenceCardStyle}
      variant={selected ? 'Surface' : 'SurfaceVariant'}
      direction="Column"
      gap="300"
      outlined={selected}
    >
      <Box alignItems="Start" gap="300" wrap="Wrap">
        <Box grow="Yes" direction="Column" gap="100" style={{ minWidth: 0 }}>
          <Text className={BreakWord} size="T400">
            {accountDisplayName(account)}
          </Text>
          <Text className={BreakWord} size="T200" priority="300">
            {account.user_id}
          </Text>
          {!account.role && (
            <Text className={BreakWord} size="T200" priority="300">
              {ROLE_LABEL.none}
            </Text>
          )}
        </Box>
        <AccountStatusChip account={account} />
      </Box>
      <Box gap="200" wrap="Wrap">
        <Button
          type="button"
          size="300"
          variant="Secondary"
          fill="Soft"
          radii="300"
          before={<Icon src={Icons.Pencil} size="100" />}
          disabled={disabled || deactivated}
          onClick={() => onEdit(account)}
        >
          <Text size="B300">Editar</Text>
        </Button>
        <Button
          type="button"
          size="300"
          variant="Secondary"
          fill="Soft"
          radii="300"
          before={<Icon src={Icons.Lock} size="100" />}
          disabled={disabled || deactivated}
          onClick={() => onPasswordReset(account)}
        >
          <Text size="B300">Redefinir senha</Text>
        </Button>
        <Button
          type="button"
          size="300"
          variant="Warning"
          fill="Soft"
          radii="300"
          before={<Icon src={Icons.Prohibited} size="100" />}
          disabled={disabled || deactivated || suspended}
          onClick={() => onToggleLocked(account)}
        >
          <Text size="B300">{blocked ? 'Reativar' : 'Bloquear/desativar'}</Text>
        </Button>
        <Button
          type="button"
          size="300"
          variant="Critical"
          fill="Soft"
          radii="300"
          before={<Icon src={Icons.Delete} size="100" />}
          disabled={disabled || deactivated}
          onClick={() => onDelete(account)}
        >
          <Text size="B300">Excluir</Text>
        </Button>
      </Box>
    </SequenceCard>
  );
}

type AdministrationProps = {
  requestClose: () => void;
};
export function Administration({ requestClose }: AdministrationProps) {
  const mx = useMatrixClient();
  const clientConfig = useClientConfig();
  const backendUrl = administrationBackendUrl(clientConfig);
  const accessToken = mx.getAccessToken();

  const [accounts, setAccounts] = useState<AdminAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [notice, setNotice] = useState<string>();
  const [activationUrl, setActivationUrl] = useState<string>();
  const [query, setQuery] = useState('');
  const [username, setUsername] = useState('');
  const [role, setRole] = useState<CreatableAccountRole>('user');
  const [editingAccount, setEditingAccount] = useState<AdminAccount>();
  const [editingDisplayName, setEditingDisplayName] = useState('');
  const [passwordAccount, setPasswordAccount] = useState<AdminAccount>();
  const [newPassword, setNewPassword] = useState('');

  const load = useCallback(async () => {
    if (!accessToken) {
      setError('Sessão Matrix sem token de acesso.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(undefined);
    try {
      const response = await listAccounts(backendUrl, accessToken);
      setAccounts(response.accounts);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }, [accessToken, backendUrl]);

  useEffect(() => {
    load();
  }, [load]);

  const filteredAccounts = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return accounts;

    return accounts.filter(
      (account) =>
        account.user_id.toLowerCase().includes(term) ||
        accountDisplayName(account).toLowerCase().includes(term) ||
        ROLE_LABEL[account.role ?? 'none'].toLowerCase().includes(term)
    );
  }, [accounts, query]);

  const runOperation = async (operation: () => Promise<void>, successMessage: string) => {
    setBusy(true);
    setError(undefined);
    setNotice(undefined);
    try {
      await operation();
      setNotice(successMessage);
      await load();
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  const handleUsernameChange: ChangeEventHandler<HTMLInputElement> = (evt) => {
    setUsername(evt.target.value);
  };

  const handleQueryChange: ChangeEventHandler<HTMLInputElement> = (evt) => {
    setQuery(evt.target.value);
  };

  const handleEditingDisplayNameChange: ChangeEventHandler<HTMLInputElement> = (evt) => {
    setEditingDisplayName(evt.target.value);
  };

  const handlePasswordChange: ChangeEventHandler<HTMLInputElement> = (evt) => {
    setNewPassword(evt.target.value);
  };

  const handleCreate: FormEventHandler<HTMLFormElement> = (evt) => {
    evt.preventDefault();
    if (!accessToken) return;

    runOperation(async () => {
      const issued = await issueActivation(backendUrl, accessToken, username, role);
      setActivationUrl(issued.invite_url);
      setUsername('');
      setRole('user');
    }, 'Ativação emitida.');
  };

  const handleEdit = (account: AdminAccount) => {
    setPasswordAccount(undefined);
    setEditingAccount(account);
    setEditingDisplayName(account.display_name ?? '');
  };

  const handleSaveEdit: FormEventHandler<HTMLFormElement> = (evt) => {
    evt.preventDefault();
    if (!accessToken || !editingAccount) return;

    runOperation(async () => {
      await updateAccount(backendUrl, accessToken, editingAccount.user_id, {
        display_name: editingDisplayName,
      });
      setEditingAccount(undefined);
      setEditingDisplayName('');
    }, 'Conta atualizada.');
  };

  const handlePasswordReset = (account: AdminAccount) => {
    setEditingAccount(undefined);
    setPasswordAccount(account);
    setNewPassword('');
  };

  const handleSavePassword: FormEventHandler<HTMLFormElement> = (evt) => {
    evt.preventDefault();
    if (!accessToken || !passwordAccount) return;

    runOperation(async () => {
      await resetAccountPassword(backendUrl, accessToken, passwordAccount.user_id, newPassword);
      setPasswordAccount(undefined);
      setNewPassword('');
    }, 'Senha redefinida.');
  };

  const handleToggleLocked = (account: AdminAccount) => {
    if (!accessToken) return;
    const locked = !account.locked;
    runOperation(
      async () => {
        await updateAccount(backendUrl, accessToken, account.user_id, { locked });
      },
      locked ? 'Conta bloqueada.' : 'Conta reativada.'
    );
  };

  const handleDelete = (account: AdminAccount) => {
    if (!accessToken) return;
    runOperation(
      () => deactivateAccount(backendUrl, accessToken, account.user_id),
      'Conta desativada.'
    );
  };

  return (
    <Page>
      <PageHeader outlined={false}>
        <Box grow="Yes" gap="200">
          <Box grow="Yes" alignItems="Center" gap="200">
            <Text size="H3" truncate>
              Administração
            </Text>
          </Box>
          <Box shrink="No">
            <IconButton onClick={requestClose} variant="Surface">
              <Icon src={Icons.Cross} />
            </IconButton>
          </Box>
        </Box>
      </PageHeader>
      <Box grow="Yes">
        <Scroll hideTrack visibility="Hover">
          <PageContent>
            <Box direction="Column" gap="700">
              {(error || notice) && (
                <SequenceCard
                  className={SequenceCardStyle}
                  variant="SurfaceVariant"
                  direction="Column"
                  gap="400"
                >
                  <Text size="T300" priority={error ? '500' : '300'}>
                    {error ?? notice}
                  </Text>
                </SequenceCard>
              )}

              <Box direction="Column" gap="100">
                <Text size="L400">Criar conta</Text>
                <SequenceCard
                  as="form"
                  className={SequenceCardStyle}
                  variant="SurfaceVariant"
                  direction="Column"
                  gap="400"
                  onSubmit={handleCreate}
                >
                  <SettingTile
                    title="Ativação"
                    description="A conta será criada quando o usuário abrir o link e escolher a própria senha."
                  >
                    <Box direction="Column" gap="300">
                      <Input
                        required
                        name="adminCreateUsername"
                        value={username}
                        onChange={handleUsernameChange}
                        before={<Icon src={Icons.User} size="100" />}
                        variant="Secondary"
                        radii="300"
                        autoComplete="off"
                        disabled={busy}
                      />
                      <Box gap="200" wrap="Wrap">
                        <RoleButton
                          accountRole="user"
                          selected={role === 'user'}
                          disabled={busy}
                          onSelect={setRole}
                        />
                        <RoleButton
                          accountRole="group_admin"
                          selected={role === 'group_admin'}
                          disabled={busy}
                          onSelect={setRole}
                        />
                      </Box>
                      <Box justifyContent="End">
                        <Button
                          type="submit"
                          size="300"
                          variant="Primary"
                          radii="300"
                          disabled={busy || !accessToken}
                          before={<Icon src={Icons.UserPlus} size="100" />}
                        >
                          {busy && <Spinner variant="Primary" fill="Solid" size="200" />}
                          <Text size="B300">Emitir ativação</Text>
                        </Button>
                      </Box>
                    </Box>
                  </SettingTile>
                </SequenceCard>
                {activationUrl && (
                  <SequenceCard
                    className={SequenceCardStyle}
                    variant="SurfaceVariant"
                    direction="Column"
                    gap="300"
                  >
                    <Text size="T300">Link de ativação emitido</Text>
                    <Input
                      readOnly
                      value={activationUrl}
                      name="adminActivationUrl"
                      variant="Secondary"
                      radii="300"
                    />
                  </SequenceCard>
                )}
              </Box>

              {editingAccount && (
                <Box direction="Column" gap="100">
                  <Text size="L400">Editar conta</Text>
                  <SequenceCard
                    as="form"
                    className={SequenceCardStyle}
                    variant="SurfaceVariant"
                    direction="Column"
                    gap="400"
                    onSubmit={handleSaveEdit}
                  >
                    <SettingTile
                      title={editingAccount.user_id}
                      description={ROLE_LABEL[editingAccount.role ?? 'none']}
                    >
                      <Box gap="200" wrap="Wrap">
                        <Box grow="Yes" direction="Column" style={{ minWidth: 0 }}>
                          <Input
                            required
                            name="adminEditDisplayName"
                            value={editingDisplayName}
                            onChange={handleEditingDisplayNameChange}
                            variant="Secondary"
                            radii="300"
                            autoComplete="off"
                            disabled={busy}
                          />
                        </Box>
                        <Button
                          type="submit"
                          size="300"
                          variant="Success"
                          radii="300"
                          disabled={busy}
                        >
                          <Text size="B300">Salvar</Text>
                        </Button>
                        <Button
                          type="button"
                          size="300"
                          variant="Secondary"
                          fill="Soft"
                          radii="300"
                          disabled={busy}
                          onClick={() => setEditingAccount(undefined)}
                        >
                          <Text size="B300">Cancelar</Text>
                        </Button>
                      </Box>
                    </SettingTile>
                  </SequenceCard>
                </Box>
              )}

              {passwordAccount && (
                <Box direction="Column" gap="100">
                  <Text size="L400">Redefinir senha</Text>
                  <SequenceCard
                    as="form"
                    className={SequenceCardStyle}
                    variant="SurfaceVariant"
                    direction="Column"
                    gap="400"
                    onSubmit={handleSavePassword}
                  >
                    <SettingTile title={passwordAccount.user_id}>
                      <Box gap="200" wrap="Wrap">
                        <Box grow="Yes" direction="Column" style={{ minWidth: 0 }}>
                          <Input
                            required
                            type="password"
                            name="adminPasswordReset"
                            value={newPassword}
                            onChange={handlePasswordChange}
                            variant="Secondary"
                            radii="300"
                            autoComplete="new-password"
                            disabled={busy}
                          />
                        </Box>
                        <Button
                          type="submit"
                          size="300"
                          variant="Warning"
                          radii="300"
                          disabled={busy}
                        >
                          <Text size="B300">Redefinir</Text>
                        </Button>
                        <Button
                          type="button"
                          size="300"
                          variant="Secondary"
                          fill="Soft"
                          radii="300"
                          disabled={busy}
                          onClick={() => setPasswordAccount(undefined)}
                        >
                          <Text size="B300">Cancelar</Text>
                        </Button>
                      </Box>
                    </SettingTile>
                  </SequenceCard>
                </Box>
              )}

              <Box direction="Column" gap="100">
                <Box alignItems="Center" gap="200" wrap="Wrap">
                  <Text size="L400">Contas</Text>
                  <Chip as="span" variant="Secondary" fill="Soft" radii="Pill">
                    <Text size="B300">{accounts.length}</Text>
                  </Chip>
                  <Button
                    type="button"
                    size="300"
                    variant="Secondary"
                    fill="Soft"
                    radii="300"
                    disabled={loading || busy}
                    onClick={load}
                  >
                    <Text size="B300">Atualizar</Text>
                  </Button>
                </Box>
                <Input
                  name="adminAccountSearch"
                  value={query}
                  onChange={handleQueryChange}
                  before={<Icon src={Icons.Search} size="100" />}
                  variant="SurfaceVariant"
                  radii="300"
                  placeholder="Buscar conta"
                  autoComplete="off"
                />
                <Box direction="Column" gap="200">
                  {loading && (
                    <SequenceCard
                      className={SequenceCardStyle}
                      variant="SurfaceVariant"
                      direction="Column"
                      gap="400"
                    >
                      <Box gap="200" alignItems="Center">
                        <Spinner variant="Secondary" size="300" />
                        <Text size="T300" priority="300">
                          Carregando contas
                        </Text>
                      </Box>
                    </SequenceCard>
                  )}
                  {!loading &&
                    filteredAccounts.map((account) => (
                      <AccountRow
                        key={account.user_id}
                        account={account}
                        selected={
                          account.user_id === editingAccount?.user_id ||
                          account.user_id === passwordAccount?.user_id
                        }
                        disabled={busy}
                        onEdit={handleEdit}
                        onPasswordReset={handlePasswordReset}
                        onToggleLocked={handleToggleLocked}
                        onDelete={handleDelete}
                      />
                    ))}
                  {!loading && filteredAccounts.length === 0 && (
                    <SequenceCard
                      className={SequenceCardStyle}
                      variant="SurfaceVariant"
                      direction="Column"
                      gap="400"
                    >
                      <Text size="T300" priority="300">
                        Nenhuma conta encontrada.
                      </Text>
                    </SequenceCard>
                  )}
                </Box>
              </Box>
            </Box>
          </PageContent>
        </Scroll>
      </Box>
    </Page>
  );
}
