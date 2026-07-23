# Visão do projeto

## Objetivo

Criar um sistema web privado de comunicação corporativa, acessível pelo navegador e opcionalmente instalável como PWA. Somente pessoas autorizadas pela organização poderão utilizar o sistema.

## Público

- Funcionários da organização.
- Administradores responsáveis por contas, grupos e políticas.
- Auditores autorizados, caso a organização adote esse perfil.

## MVP

- Ativação de identidade previamente definida por `platform_admin` e login
  Matrix controlado, conforme decisão conjunta `DEC-022`.
- Diretório interno de usuários.
- Conversas individuais.
- Grupos privados.
- Mensagens em tempo real.
- Histórico paginado.
- Confirmação de entrega e leitura.
- Indicador de digitação e presença.
- Envio de imagens e documentos.
- Gravação, envio e reprodução de mensagens de voz.
- Painel administrativo básico.
- Registro de ações administrativas.
- Criptografia ponta a ponta conforme a política híbrida aprovada.
- Interface responsiva para computador e celular.

## Fora do MVP

- Canais públicos.
- Comunicação com usuários externos.
- Bots públicos.
- Chamadas de voz e vídeo.
- Federação com outras organizações.
- Compatibilidade com a rede Telegram.

A prova de conceito futura de chamadas não altera esse limite: chamadas de voz
e vídeo continuam fora do MVP até a conclusão e aprovação de um marco próprio.

## Requisitos principais

- Nenhum cadastro público.
- Usuários comuns e `group_admin` não podem escolher ou criar identidades.
- Links de ativação concedem somente a identidade e o papel `user` ou
  `group_admin` definidos previamente pelo `platform_admin`.
- O administrador nunca define nem conhece a senha do funcionário.
- Todo acesso deve ser autenticado e autorizado.
- Dados armazenados em infraestrutura controlada pela organização.
- Arquivos protegidos por autorização e URLs temporárias.
- Operações administrativas auditáveis.
- Política de retenção definida antes da produção.
- Marca e identidade visual próprias.

## Ativação de identidade aprovada

`DEC-022`, aceita pelos dois colaboradores, substitui o convite em que o
funcionário escolhe `username` por ativação de uma identidade previamente
definida. Contrato, persistência, segurança da página e limites do mecanismo
create-only foram aprovados como desenho. Cada implementação, migração e
publicação continua dependente de autorização específica.

## Fases

1. Viabilidade, licenças e contratos técnicos.
2. Prova de conceito do Matrix/Synapse.
3. Fundação da interface e da plataforma auto-hospedada.
4. Conversas, mensagens, estados em tempo real e mídia.
5. Administração e login corporativo.
6. Segurança, homologação e implantação.

## Critério de sucesso do MVP

Um grupo piloto deve conseguir entrar, iniciar conversas privadas, criar grupos, trocar mensagens e arquivos e recuperar o histórico em uma plataforma Matrix controlada pela organização, sem qualquer dependência da rede Telegram.
