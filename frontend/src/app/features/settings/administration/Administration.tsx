import React, { ChangeEventHandler, FormEventHandler, useMemo, useState } from 'react';
import { Box, Button, Chip, Icon, IconButton, Icons, Input, Scroll, Text } from 'folds';
import { Page, PageContent, PageHeader } from '../../../components/page';
import { SequenceCard } from '../../../components/sequence-card';
import { SettingTile } from '../../../components/setting-tile';
import { BreakWord } from '../../../styles/Text.css';
import { SequenceCardStyle } from '../styles.css';

type AccountRole = 'user' | 'group_admin' | 'platform_admin';
type CreatableAccountRole = Exclude<AccountRole, 'platform_admin'>;
type AccountStatus = 'active' | 'deactivated';

type ManagedAccount = {
  id: string;
  userId: string;
  displayName: string;
  role: AccountRole;
  status: AccountStatus;
  passwordResetRequested: boolean;
};

const ROLE_LABEL: Record<AccountRole, string> = {
  user: 'Usuário',
  group_admin: 'Admin de grupo',
  platform_admin: 'Administração da plataforma',
};

const STATUS_LABEL: Record<AccountStatus, string> = {
  active: 'Ativa',
  deactivated: 'Bloqueada/desativada',
};

const INITIAL_ACCOUNTS: ManagedAccount[] = [
  {
    id: 'admin',
    userId: '@admin:localhost',
    displayName: 'Administrador',
    role: 'platform_admin',
    status: 'active',
    passwordResetRequested: false,
  },
  {
    id: 'maria',
    userId: '@maria:localhost',
    displayName: 'Maria Oliveira',
    role: 'group_admin',
    status: 'active',
    passwordResetRequested: false,
  },
  {
    id: 'joao',
    userId: '@joao:localhost',
    displayName: 'Joao Santos',
    role: 'user',
    status: 'deactivated',
    passwordResetRequested: true,
  },
];

const makeLocalUserId = (username: string): string => {
  const normalized = username.trim().replace(/^@/, '').split(':')[0].toLowerCase();
  return `@${normalized}:localhost`;
};

type RoleButtonProps = {
  accountRole: CreatableAccountRole;
  selected: boolean;
  onSelect: (accountRole: CreatableAccountRole) => void;
};
function RoleButton({ accountRole, selected, onSelect }: RoleButtonProps) {
  return (
    <Button
      type="button"
      size="300"
      radii="300"
      variant={selected ? 'Primary' : 'Secondary'}
      fill={selected ? 'Solid' : 'Soft'}
      outlined={!selected}
      aria-pressed={selected}
      onClick={() => onSelect(accountRole)}
    >
      <Text size="B300">{ROLE_LABEL[accountRole]}</Text>
    </Button>
  );
}

type AccountStatusChipProps = {
  account: ManagedAccount;
};
function AccountStatusChip({ account }: AccountStatusChipProps) {
  return (
    <Box gap="100" wrap="Wrap">
      <Chip as="span" variant="Secondary" fill="Soft" radii="Pill">
        <Text size="B300">{STATUS_LABEL[account.status]}</Text>
      </Chip>
      {account.passwordResetRequested && (
        <Chip as="span" variant="Secondary" fill="Soft" radii="Pill">
          <Text size="B300">Senha pendente</Text>
        </Chip>
      )}
    </Box>
  );
}

type AccountRowProps = {
  account: ManagedAccount;
  selected: boolean;
  onEdit: (account: ManagedAccount) => void;
  onPasswordReset: (accountId: string) => void;
  onToggleStatus: (accountId: string) => void;
  onDelete: (accountId: string) => void;
};
function AccountRow({
  account,
  selected,
  onEdit,
  onPasswordReset,
  onToggleStatus,
  onDelete,
}: AccountRowProps) {
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
            {account.displayName}
          </Text>
          <Text className={BreakWord} size="T200" priority="300">
            {account.userId}
          </Text>
          <Text className={BreakWord} size="T200" priority="300">
            {ROLE_LABEL[account.role]}
          </Text>
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
          onClick={() => onPasswordReset(account.id)}
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
          onClick={() => onToggleStatus(account.id)}
        >
          <Text size="B300">{account.status === 'active' ? 'Bloquear/desativar' : 'Reativar'}</Text>
        </Button>
        <Button
          type="button"
          size="300"
          variant="Critical"
          fill="Soft"
          radii="300"
          before={<Icon src={Icons.Delete} size="100" />}
          onClick={() => onDelete(account.id)}
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
  const [accounts, setAccounts] = useState<ManagedAccount[]>(INITIAL_ACCOUNTS);
  const [query, setQuery] = useState('');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState<CreatableAccountRole>('user');
  const [editingAccountId, setEditingAccountId] = useState<string>();
  const [editingDisplayName, setEditingDisplayName] = useState('');

  const filteredAccounts = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return accounts;

    return accounts.filter(
      (account) =>
        account.userId.toLowerCase().includes(term) ||
        account.displayName.toLowerCase().includes(term) ||
        ROLE_LABEL[account.role].toLowerCase().includes(term)
    );
  }, [accounts, query]);

  const editingAccount = accounts.find((account) => account.id === editingAccountId);

  const handleUsernameChange: ChangeEventHandler<HTMLInputElement> = (evt) => {
    setUsername(evt.target.value);
  };

  const handleDisplayNameChange: ChangeEventHandler<HTMLInputElement> = (evt) => {
    setDisplayName(evt.target.value);
  };

  const handleQueryChange: ChangeEventHandler<HTMLInputElement> = (evt) => {
    setQuery(evt.target.value);
  };

  const handleEditingDisplayNameChange: ChangeEventHandler<HTMLInputElement> = (evt) => {
    setEditingDisplayName(evt.target.value);
  };

  const handleCreate: FormEventHandler<HTMLFormElement> = (evt) => {
    evt.preventDefault();

    const userId = makeLocalUserId(username);
    const localPart = userId.slice(1).split(':')[0];
    if (!localPart) return;
    if (accounts.some((account) => account.userId === userId)) return;

    const newAccount: ManagedAccount = {
      id: `${localPart}-${Date.now()}`,
      userId,
      displayName: displayName.trim() || localPart,
      role,
      status: 'active',
      passwordResetRequested: false,
    };

    setAccounts((currentAccounts) => [newAccount, ...currentAccounts]);
    setUsername('');
    setDisplayName('');
    setRole('user');
  };

  const handleEdit = (account: ManagedAccount) => {
    setEditingAccountId(account.id);
    setEditingDisplayName(account.displayName);
  };

  const handleSaveEdit: FormEventHandler<HTMLFormElement> = (evt) => {
    evt.preventDefault();
    if (!editingAccount) return;

    setAccounts((currentAccounts) =>
      currentAccounts.map((account) =>
        account.id === editingAccount.id
          ? { ...account, displayName: editingDisplayName.trim() || account.displayName }
          : account
      )
    );
    setEditingAccountId(undefined);
    setEditingDisplayName('');
  };

  const handlePasswordReset = (accountId: string) => {
    setAccounts((currentAccounts) =>
      currentAccounts.map((account) =>
        account.id === accountId ? { ...account, passwordResetRequested: true } : account
      )
    );
  };

  const handleToggleStatus = (accountId: string) => {
    setAccounts((currentAccounts) =>
      currentAccounts.map((account) =>
        account.id === accountId
          ? {
              ...account,
              status: account.status === 'active' ? 'deactivated' : 'active',
            }
          : account
      )
    );
  };

  const handleDelete = (accountId: string) => {
    setAccounts((currentAccounts) => currentAccounts.filter((account) => account.id !== accountId));
    if (editingAccountId === accountId) {
      setEditingAccountId(undefined);
      setEditingDisplayName('');
    }
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
                  <Box gap="300" wrap="Wrap">
                    <Box direction="Column" gap="100" grow="Yes" style={{ minWidth: 0 }}>
                      <Text size="T300">Nome de usuário</Text>
                      <Input
                        required
                        name="adminCreateUsername"
                        value={username}
                        onChange={handleUsernameChange}
                        before={<Icon src={Icons.User} size="100" />}
                        variant="Secondary"
                        radii="300"
                        autoComplete="off"
                      />
                    </Box>
                    <Box direction="Column" gap="100" grow="Yes" style={{ minWidth: 0 }}>
                      <Text size="T300">Nome de exibição</Text>
                      <Input
                        name="adminCreateDisplayName"
                        value={displayName}
                        onChange={handleDisplayNameChange}
                        before={<Icon src={Icons.Pencil} size="100" />}
                        variant="Secondary"
                        radii="300"
                        autoComplete="off"
                      />
                    </Box>
                  </Box>
                  <Box direction="Column" gap="100">
                    <Text size="T300">Papel</Text>
                    <Box gap="200" wrap="Wrap">
                      <RoleButton
                        accountRole="user"
                        selected={role === 'user'}
                        onSelect={setRole}
                      />
                      <RoleButton
                        accountRole="group_admin"
                        selected={role === 'group_admin'}
                        onSelect={setRole}
                      />
                    </Box>
                  </Box>
                  <Box justifyContent="End">
                    <Button
                      type="submit"
                      size="300"
                      variant="Primary"
                      radii="300"
                      before={<Icon src={Icons.UserPlus} size="100" />}
                    >
                      <Text size="B300">Criar</Text>
                    </Button>
                  </Box>
                </SequenceCard>
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
                      title={editingAccount.userId}
                      description={ROLE_LABEL[editingAccount.role]}
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
                          />
                        </Box>
                        <Button type="submit" size="300" variant="Success" radii="300">
                          <Text size="B300">Salvar</Text>
                        </Button>
                        <Button
                          type="button"
                          size="300"
                          variant="Secondary"
                          fill="Soft"
                          radii="300"
                          onClick={() => setEditingAccountId(undefined)}
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
                  {filteredAccounts.map((account) => (
                    <AccountRow
                      key={account.id}
                      account={account}
                      selected={account.id === editingAccountId}
                      onEdit={handleEdit}
                      onPasswordReset={handlePasswordReset}
                      onToggleStatus={handleToggleStatus}
                      onDelete={handleDelete}
                    />
                  ))}
                  {filteredAccounts.length === 0 && (
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
