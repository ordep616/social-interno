# Instruções locais — frontend

## Finalidade

Esta pasta é a raiz do fork corporativo do Cinny `v4.12.3`. Ela pertence ao
Colaborador 2. Leia `CORPORATE_FORK.md` antes de modificar o código.

## Regras

- Preserve `LICENSE`, autoria, origem e obrigações da AGPL-3.0-only.
- Preserve o máximo possível da estrutura e da integração Matrix originais.
- Mantenha alterações corporativas pequenas e fáceis de comparar com o upstream.
- Não reintroduza seleção de homeserver, cadastro público ou descoberta pública.
- Não aponte o cliente para servidores Matrix externos.
- Não altere `../platform/` ou `../backend/` para contornar problemas do frontend.
- Nome definitivo, OIDC, criptografia e recursos fora do MVP exigem decisão aprovada.
- Registre novas dependências e ativos em `../docs/OPEN_SOURCE.md`.

## Validação

Execute build, verificações aplicáveis e teste contra um homeserver de
desenvolvimento. Problemas herdados do upstream devem ser registrados
separadamente das regressões introduzidas pelo fork.
