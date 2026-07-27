import React, { FormEventHandler, useCallback, useEffect, useRef, useState } from 'react';
import { Box, Button, Icon, Icons, Input, Spinner, Text, color, config } from 'folds';
import { useNavigate } from 'react-router-dom';

import { PasswordInput } from '../../../components/password-input';
import { useClientConfig } from '../../../hooks/useClientConfig';
import { FieldError } from '../FiledError';
import { getLoginPath, withSearchParam } from '../../pathUtils';
import {
  ActivationApiError,
  ActivationRole,
  ActivationValidationResponse,
  activationBackendUrl,
  registerActivation,
  validateActivation,
} from './api';

const ROLE_LABEL: Record<ActivationRole, string> = {
  user: 'Usuário',
  group_admin: 'Admin de grupo',
};

type ActivationState =
  | {
      status: 'reading';
    }
  | {
      status: 'loading';
    }
  | {
      status: 'missing';
    }
  | {
      status: 'ready';
      activation: ActivationValidationResponse;
    }
  | {
      status: 'success';
    }
  | {
      status: 'error';
      error: unknown;
    };

type ErrorCopy = {
  title: string;
  message: string;
};

const readActivationTokenFromLocation = (): string => {
  const { hash } = window.location;
  if (!hash.startsWith('#')) return '';

  return hash.slice(1);
};

const removeActivationHashFromLocation = () => {
  const { pathname } = window.location;
  window.history.replaceState(window.history.state, document.title, pathname);
};

const formatExpiration = (expiresAt: string): string => {
  const date = new Date(expiresAt);
  if (Number.isNaN(date.getTime())) return expiresAt;

  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(date);
};

const getPasswordError = (password: string): string | undefined => {
  if (password.length < 15) return 'A senha precisa ter pelo menos 15 caracteres.';
  if (password.length > 128) return 'A senha pode ter no máximo 128 caracteres.';
  return undefined;
};

const getActivationErrorCopy = (error: unknown): ErrorCopy => {
  if (error instanceof ActivationApiError) {
    if (error.code === 'activation_not_found' || error.code === 'activation_unavailable') {
      return {
        title: 'Link de ativação indisponível',
        message: 'O link está inválido, expirado, usado ou revogado.',
      };
    }
    if (error.code === 'activation_conflict') {
      return {
        title: 'Identidade indisponível',
        message: 'A conta definida para este link precisa ser revisada pela administração.',
      };
    }
    if (error.code === 'rate_limited') {
      return {
        title: 'Muitas tentativas',
        message: 'Aguarde alguns minutos antes de tentar ativar a conta novamente.',
      };
    }
    if (error.code === 'password_policy_violation') {
      return {
        title: 'Senha não aceita',
        message: 'Use uma senha entre 15 e 128 caracteres.',
      };
    }
    if (error.code === 'invalid_request') {
      return {
        title: 'Solicitação inválida',
        message: 'Abra novamente o link enviado pela administração.',
      };
    }
    if (error.code === 'access_denied') {
      return {
        title: 'Acesso negado',
        message: 'O serviço recusou esta ativação.',
      };
    }
    if (error.code === 'upstream_invalid_response') {
      return {
        title: 'Resposta inesperada',
        message: 'O serviço de ativação respondeu fora do contrato combinado.',
      };
    }
    if (error.code === 'service_unavailable') {
      return {
        title: 'Serviço de ativação indisponível',
        message: 'Não foi possível concluir a ativação agora.',
      };
    }
  }

  return {
    title: 'Serviço de ativação indisponível',
    message: 'Não foi possível conectar ao serviço de ativação agora.',
  };
};

const useActivationReferrerPolicy = () => {
  useEffect(() => {
    const existingMeta = document.querySelector<HTMLMetaElement>('meta[name="referrer"]');
    const meta = existingMeta ?? document.createElement('meta');
    const previousContent = existingMeta?.getAttribute('content');

    if (!existingMeta) {
      meta.setAttribute('name', 'referrer');
      document.head.append(meta);
    }
    meta.setAttribute('content', 'no-referrer');

    return () => {
      if (existingMeta) {
        if (previousContent === null || previousContent === undefined) {
          existingMeta.removeAttribute('content');
          return;
        }
        existingMeta.setAttribute('content', previousContent);
        return;
      }
      meta.remove();
    };
  }, []);
};

type ActivationMessageProps = {
  title: string;
  message: string;
  children?: React.ReactNode;
};
function ActivationMessage({ title, message, children }: ActivationMessageProps) {
  return (
    <Box direction="Column" gap="400">
      <Box direction="Column" gap="200" alignItems="Center">
        <Icon size="300" filled src={Icons.Warning} />
        <Text size="H2" priority="400" align="Center">
          {title}
        </Text>
        <Text size="T300" priority="300" align="Center">
          {message}
        </Text>
      </Box>
      {children}
    </Box>
  );
}

type ActivationLoadingProps = {
  message: string;
};
function ActivationLoading({ message }: ActivationLoadingProps) {
  return (
    <Box direction="Column" justifyContent="Center" alignItems="Center" gap="300">
      <Spinner size="300" variant="Secondary" />
      <Text size="T300" priority="300" align="Center">
        {message}
      </Text>
    </Box>
  );
}

export function Activate() {
  useActivationReferrerPolicy();

  const navigate = useNavigate();
  const clientConfig = useClientConfig();
  const backendUrl = activationBackendUrl(clientConfig);
  const tokenRef = useRef<string>();
  const tokenReadRef = useRef(false);
  const aliveRef = useRef(true);

  const [activationState, setActivationState] = useState<ActivationState>({
    status: 'reading',
  });
  const [submitting, setSubmitting] = useState(false);
  const [passwordError, setPasswordError] = useState<string>();
  const [submissionError, setSubmissionError] = useState<unknown>();

  useEffect(
    () => () => {
      aliveRef.current = false;
    },
    []
  );

  const loadActivation = useCallback(
    async (token: string) => {
      setActivationState({ status: 'loading' });
      setPasswordError(undefined);
      setSubmissionError(undefined);

      try {
        const activation = await validateActivation(backendUrl, token);
        if (!aliveRef.current) return;
        setActivationState({ status: 'ready', activation });
      } catch (error) {
        if (!aliveRef.current) return;
        setActivationState({ status: 'error', error });
      }
    },
    [backendUrl]
  );

  useEffect(() => {
    if (tokenReadRef.current) return;
    tokenReadRef.current = true;

    const token = readActivationTokenFromLocation();
    if (window.location.hash || window.location.search) {
      removeActivationHashFromLocation();
    }

    if (!token) {
      setActivationState({ status: 'missing' });
      return;
    }

    tokenRef.current = token;
    loadActivation(token);
  }, [loadActivation]);

  const handleRetry = () => {
    const token = tokenRef.current;
    if (!token) {
      setActivationState({ status: 'missing' });
      return;
    }

    loadActivation(token);
  };

  const handleLogin = () => {
    tokenRef.current = undefined;
    navigate(getLoginPath(), { replace: true });
  };

  const handleSubmit: FormEventHandler<HTMLFormElement> = async (evt) => {
    evt.preventDefault();
    if (activationState.status !== 'ready') return;

    const { passwordInput } = evt.currentTarget as HTMLFormElement & {
      passwordInput: HTMLInputElement;
    };

    const password = passwordInput.value;
    const localPasswordError = getPasswordError(password);

    setPasswordError(localPasswordError);
    setSubmissionError(undefined);

    if (localPasswordError) {
      passwordInput.focus();
      return;
    }

    const token = tokenRef.current;
    if (!token) {
      setActivationState({ status: 'missing' });
      return;
    }

    setSubmitting(true);
    try {
      const registration = await registerActivation(
        backendUrl,
        token,
        password,
        activationState.activation
      );

      if (registration.user_id !== activationState.activation.target_user_id) {
        throw new ActivationApiError(
          502,
          'upstream_invalid_response',
          'Resposta de ativacao fora do contrato.'
        );
      }

      const { username } = activationState.activation;
      if (!username) {
        throw new ActivationApiError(
          502,
          'upstream_invalid_response',
          'Resposta de ativacao fora do contrato.'
        );
      }

      tokenRef.current = undefined;
      passwordInput.value = '';
      setActivationState({ status: 'success' });
      navigate(withSearchParam(getLoginPath(), { username }), {
        replace: true,
      });
    } catch (error) {
      passwordInput.value = '';
      setSubmissionError(error);
      passwordInput.focus();
    } finally {
      if (aliveRef.current) {
        setSubmitting(false);
      }
    }
  };

  if (activationState.status === 'reading' || activationState.status === 'loading') {
    return <ActivationLoading message="Validando link de ativação..." />;
  }

  if (activationState.status === 'missing') {
    return (
      <ActivationMessage
        title="Link de ativação ausente"
        message="Abra o link completo enviado pela administração."
      >
        <Button
          type="button"
          size="500"
          variant="Primary"
          before={<Icon src={Icons.ArrowRight} size="100" />}
          onClick={handleLogin}
        >
          <Text as="span" size="B500">
            Ir para login
          </Text>
        </Button>
      </ActivationMessage>
    );
  }

  if (activationState.status === 'error') {
    const errorCopy = getActivationErrorCopy(activationState.error);

    return (
      <ActivationMessage title={errorCopy.title} message={errorCopy.message}>
        <Box direction="Column" gap="200">
          <Button
            type="button"
            size="500"
            variant="Primary"
            disabled={submitting}
            onClick={handleRetry}
          >
            <Text as="span" size="B500">
              Tentar novamente
            </Text>
          </Button>
          <Button
            type="button"
            size="500"
            variant="Secondary"
            before={<Icon src={Icons.ArrowRight} size="100" />}
            onClick={handleLogin}
          >
            <Text as="span" size="B500">
              Ir para login
            </Text>
          </Button>
        </Box>
      </ActivationMessage>
    );
  }

  if (activationState.status === 'success') {
    return <ActivationLoading message="Conta ativada. Redirecionando para login..." />;
  }

  const { activation } = activationState;
  const submissionErrorCopy = submissionError ? getActivationErrorCopy(submissionError) : undefined;

  return (
    <Box as="form" onSubmit={handleSubmit} direction="Column" gap="500">
      <Box direction="Column" gap="200">
        <Text size="H2" priority="400">
          Ativar conta
        </Text>
        <Text size="T300" priority="400">
          Confira a identidade definida pela organização e escolha sua senha.
        </Text>
      </Box>

      <Box direction="Column" gap="300">
        <Box direction="Column" gap="100">
          <Text as="label" htmlFor="activation-username" size="L400" priority="300">
            Usuário
          </Text>
          <Input
            id="activation-username"
            value={activation.username}
            variant="Background"
            size="500"
            readOnly
            outlined
          />
        </Box>
        <Box direction="Column" gap="100">
          <Text as="label" htmlFor="activation-role" size="L400" priority="300">
            Papel
          </Text>
          <Input
            id="activation-role"
            value={ROLE_LABEL[activation.role]}
            variant="Background"
            size="500"
            readOnly
            outlined
          />
        </Box>
        <Text size="T200" priority="300">
          Válido até {formatExpiration(activation.expires_at)}.
        </Text>
      </Box>

      <Box direction="Column" gap="100">
        <Text as="label" htmlFor="activation-password" size="L400" priority="300">
          Senha
        </Text>
        <PasswordInput
          id="activation-password"
          name="passwordInput"
          variant="Background"
          size="500"
          autoComplete="new-password"
          minLength={15}
          maxLength={128}
          required
          outlined
          autoFocus
          readOnly={submitting}
          aria-describedby="activation-password-help"
          style={passwordError ? { color: color.Critical.Main } : undefined}
        />
        <Text id="activation-password-help" size="T200" priority="300">
          Use entre 15 e 128 caracteres.
        </Text>
        {passwordError && <FieldError message={passwordError} />}
      </Box>

      {submissionErrorCopy && (
        <FieldError message={`${submissionErrorCopy.title}. ${submissionErrorCopy.message}`} />
      )}

      <Button
        type="submit"
        variant="Primary"
        size="500"
        disabled={submitting}
        before={
          submitting ? (
            <Spinner size="100" variant="Secondary" />
          ) : (
            <Icon src={Icons.Lock} size="100" />
          )
        }
        style={{ marginTop: config.space.S100 }}
      >
        <Text as="span" size="B500">
          {submitting ? 'Ativando...' : 'Ativar conta'}
        </Text>
      </Button>
    </Box>
  );
}
