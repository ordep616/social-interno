# Código aberto e licenças

Este documento é um inventário técnico inicial, não um parecer jurídico.

## Estratégia atual

O projeto adaptará uma plataforma Matrix auto-hospedada e manterá um fork corporativo do Cinny como cliente web.

## Componentes principais a avaliar

| Área                         | Orientação inicial            | Observação                                                        |
| ---------------------------- | ----------------------------- | ----------------------------------------------------------------- |
| Protocolo Matrix             | Adotar                        | Usar especificação e APIs padronizadas                            |
| Synapse                      | Prova de conceito e revisão   | Verificar versão, licença AGPL/comercial e operação               |
| Cinny                        | Adotar como fork              | Preservar licença AGPL, avisos, origem e histórico das alterações |
| `matrix-js-sdk`              | Dependência do Cinny          | Versão fixada pelo fork e revisada em cada atualização            |
| Element Web                  | Somente referência por padrão | Não copiar código antes de avaliar AGPL/GPL e dependências        |
| Telegram Web                 | Somente referência por padrão | Não é necessário para a arquitetura Matrix                        |
| FastAPI                      | Adotar no serviço auxiliar    | Convites, provisionamento e ciclo de vida aprovados               |
| Identidade e ícones oficiais | Não utilizar                  | O produto terá marca e ativos próprios                            |

## Processo de incorporação

1. Registrar repositório oficial e hash do commit ou versão da imagem.
2. Ler a licença raiz e licenças específicas.
3. Identificar dependências, imagens de contêiner e ativos associados.
4. Registrar a finalidade e a forma de integração.
5. Registrar configurações ou alterações mantidas pela equipe.
6. Obter revisão do outro colaborador.
7. Obter revisão jurídica quando houver copyleft, distribuição ou oferta pela rede relevante.
8. Preservar avisos e atribuições obrigatórias.

## Inventário

| ID     | Componente                  | Origem                                                             | Versão/commit                                                | Licença                                                                    | Uso pretendido                                        | Responsável   | Estado                                                                              |
| ------ | --------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------ | -------------------------------------------------------------------------- | ----------------------------------------------------- | ------------- | ----------------------------------------------------------------------------------- |
| OS-001 | Synapse                     | `https://github.com/element-hq/synapse`                            | `v1.156.0`                                                   | AGPL-3.0 ou licença comercial                                              | Homeserver da prova de conceito                       | Colaborador 1 | Configuração incorporada; execução e revisão jurídica pendentes                     |
| OS-002 | matrix-js-sdk               | `https://github.com/matrix-org/matrix-js-sdk`                      | `41.7.0`                                                     | Apache-2.0                                                                 | SDK utilizado pelo Cinny `v4.12.3`                    | Colaborador 2 | Dependência incorporada pelo fork                                                   |
| OS-003 | Element Web                 | A registrar se houver uso                                          | —                                                            | AGPL/GPL/comercial, a confirmar                                            | Somente referência inicial                            | Colaborador 2 | Não incorporar                                                                      |
| OS-004 | Telegram Web                | A registrar se houver uso                                          | —                                                            | GPL, a confirmar por repositório                                           | Somente referência inicial                            | Colaborador 2 | Não incorporar                                                                      |
| OS-005 | PostgreSQL                  | `https://github.com/postgres/postgres`                             | imagem `17.6-alpine`                                         | PostgreSQL License                                                         | Banco do Synapse na prova de conceito                 | Colaborador 1 | Configuração incorporada                                                            |
| OS-006 | Cinny                       | `https://github.com/cinnyapp/cinny`                                | `v4.12.3` / `69515e8e81d082a7b0609247e296391d3d6f1e38`       | AGPL-3.0-only                                                              | Base integral do cliente web corporativo              | Colaborador 2 | Incorporação aprovada pelos dois colaboradores; personalização inicial em andamento |
| OS-007 | CPython                     | `https://github.com/python/cpython`                                | `>=3.14,<3.15`; validado com `3.14.6`                         | PSF-2.0                                                                    | Runtime do serviço de convites                         | Colaborador 1 | Incorporado na fundação por `.python-version` e `pyproject.toml`                     |
| OS-008 | FastAPI                     | `https://github.com/fastapi/fastapi`                               | `0.139.2`                                                     | MIT                                                                        | Framework da API REST auxiliar                         | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-009 | Uvicorn                     | `https://github.com/Kludex/uvicorn`                                | `0.51.0`                                                      | BSD-3-Clause                                                               | Servidor ASGI do FastAPI                               | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-010 | SQLAlchemy                  | `https://github.com/sqlalchemy/sqlalchemy`                         | `2.0.51`                                                      | MIT                                                                        | ORM e transações no PostgreSQL próprio                 | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-011 | Psycopg                     | `https://github.com/psycopg/psycopg`                              | `3.3.4`; `psycopg-binary` `3.3.4`                            | LGPL-3.0-only; conteúdo binário e licenças agregadas a revisar             | Driver síncrono do PostgreSQL                          | Colaborador 1 | Fixado no `uv.lock`; revisão obrigatória antes de homologação/produção               |
| OS-012 | Alembic                     | `https://github.com/sqlalchemy/alembic`                            | `1.18.5`                                                      | MIT                                                                        | Migrações do banco próprio                             | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-013 | pydantic-settings           | `https://github.com/pydantic/pydantic-settings`                    | `2.14.2`                                                      | MIT                                                                        | Configuração por variáveis de ambiente                 | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-014 | HTTPX                       | `https://github.com/encode/httpx`                                  | `0.28.1`                                                      | BSD-3-Clause                                                               | Cliente HTTP para integração com Synapse               | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-015 | uv                          | `https://github.com/astral-sh/uv`                                  | `0.11.31`                                                     | MIT OR Apache-2.0                                                          | Ambiente, resolução e lock de dependências             | Colaborador 1 | Instalado via Homebrew; `uv.lock` incorporado                                        |
| OS-016 | Ruff                        | `https://github.com/astral-sh/ruff`                                | `0.15.22`                                                     | MIT                                                                        | Lint e formatação                                      | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-017 | mypy                        | `https://github.com/python/mypy`                                   | `1.20.2`                                                      | MIT                                                                        | Verificação estática de tipos                          | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-018 | pytest                      | `https://github.com/pytest-dev/pytest`                             | `9.1.1`                                                       | MIT                                                                        | Testes automatizados                                   | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| OS-019 | pytest-cov                  | `https://github.com/pytest-dev/pytest-cov`                         | `7.1.0`                                                       | MIT                                                                        | Cobertura dos testes                                   | Colaborador 1 | Fixado no `uv.lock`; incorporado na fundação                                         |
| AS-001 | Logo corporativa provisória | Arquivo fornecido pelo usuário em `photo_2026-07-21 13.58.16.jpeg` | JPEG 500x500; derivados PNG em múltiplos tamanhos            | Ativo próprio/provisório; direitos de uso a confirmar antes da homologação | Logo da interface, favicon e ícones PWA/Apple/Android | Colaborador 2 | Incorporado no frontend como ativo de identidade provisório                         |
| AS-002 | Logo ExplorerNet provisória | Arquivo fornecido pelo usuário em captura de tela PNG              | PNG 648x112; derivado em `frontend/public/res/logo`          | Ativo próprio/provisório; direitos de uso a confirmar antes da homologação | Assinatura visual no canto inferior direito da home   | Colaborador 2 | Incorporado no frontend como ativo de identidade provisório                         |
| AS-003 | Fundo da home provisório    | Arquivo fornecido pelo usuário em `photo_2026-07-21 17.01.55.jpeg` | JPEG 1280x853; copiado para `frontend/public/res/background` | Ativo próprio/provisório; direitos de uso a confirmar antes da homologação | Fundo visual da tela inicial do cliente web           | Colaborador 2 | Incorporado no frontend como ativo de identidade provisório                         |
| AS-004 | Logo da home provisório     | Arquivo fornecido pelo usuário em `X fundo PR.png`                 | PNG 907x907; copiado para `frontend/public/res/logo`         | Ativo próprio/provisório; direitos de uso a confirmar antes da homologação | Logo exibido acima do título da tela inicial          | Colaborador 2 | Incorporado no frontend como ativo de identidade provisório                         |

## Dependências transitivas da fundação Python

Inventário obtido da resolução `uv.lock` e dos metadados instalados em 2026-07-22. Dependências com licença de copyleft fraco permanecem sujeitas à revisão prevista antes da homologação.

| ID | Componente | Origem | Versão | Licença | Introduzido por |
| --- | --- | --- | --- | --- | --- |
| PY-T001 | annotated-doc | `https://github.com/fastapi/annotated-doc` | `0.0.4` | MIT | FastAPI |
| PY-T002 | annotated-types | `https://github.com/annotated-types/annotated-types` | `0.7.0` | MIT | Pydantic |
| PY-T003 | anyio | `https://github.com/agronholm/anyio` | `4.14.2` | MIT | Starlette e HTTPX |
| PY-T004 | certifi | `https://github.com/certifi/python-certifi` | `2026.7.22` | MPL-2.0 | HTTPX |
| PY-T005 | click | `https://github.com/pallets/click` | `8.4.2` | BSD-3-Clause | Uvicorn |
| PY-T006 | coverage | `https://github.com/nedbat/coveragepy` | `7.15.2` | Apache-2.0 | pytest-cov |
| PY-T007 | h11 | `https://github.com/python-hyper/h11` | `0.16.0` | MIT | Uvicorn e HTTPX |
| PY-T008 | httpcore | `https://github.com/encode/httpcore` | `1.0.9` | BSD-3-Clause | HTTPX |
| PY-T009 | idna | `https://github.com/kjd/idna` | `3.18` | BSD-3-Clause | AnyIO e HTTPX |
| PY-T010 | iniconfig | `https://github.com/pytest-dev/iniconfig` | `2.3.0` | MIT | pytest |
| PY-T011 | librt | `https://github.com/mypyc/librt` | `0.13.0` | MIT | mypy |
| PY-T012 | Mako | `https://github.com/sqlalchemy/mako` | `1.3.12` | MIT | Alembic |
| PY-T013 | MarkupSafe | `https://github.com/pallets/markupsafe` | `3.0.3` | BSD-3-Clause | Mako |
| PY-T014 | mypy-extensions | `https://github.com/python/mypy_extensions` | `1.1.0` | MIT | mypy |
| PY-T015 | packaging | `https://github.com/pypa/packaging` | `26.2` | Apache-2.0 OR BSD-2-Clause | pytest |
| PY-T016 | pathspec | `https://github.com/cpburnz/python-pathspec` | `1.1.1` | MPL-2.0 | mypy |
| PY-T017 | pluggy | `https://github.com/pytest-dev/pluggy` | `1.6.0` | MIT | pytest |
| PY-T018 | Pydantic | `https://github.com/pydantic/pydantic` | `2.13.4` | MIT | FastAPI e pydantic-settings |
| PY-T019 | pydantic-core | `https://github.com/pydantic/pydantic-core` | `2.46.4` | MIT | Pydantic |
| PY-T020 | Pygments | `https://github.com/pygments/pygments` | `2.20.0` | BSD-2-Clause | pytest |
| PY-T021 | python-dotenv | `https://github.com/theskumar/python-dotenv` | `1.2.2` | BSD-3-Clause | pydantic-settings |
| PY-T022 | Starlette | `https://github.com/Kludex/starlette` | `1.3.1` | BSD-3-Clause | FastAPI |
| PY-T023 | typing-inspection | `https://github.com/pydantic/typing-inspection` | `0.4.2` | MIT | Pydantic |
| PY-T024 | typing-extensions | `https://github.com/python/typing_extensions` | `4.16.0` | PSF-2.0 | FastAPI, SQLAlchemy e Pydantic |

## Regra de isolamento

- A integração Matrix seguirá a arquitetura interna do Cinny; novas integrações próprias não devem acoplar componentes corporativos diretamente ao SDK sem necessidade.
- Alterações de configuração do Synapse devem ficar rastreáveis na área `platform/`.
- Código copiado de terceiros deve preservar origem, licença e alterações.
- Não importar código do Element ou Telegram apenas por semelhança visual.
- Não usar MTProto, GramJS, TDLib, `api_id`, `api_hash` ou infraestrutura do Telegram.

## Revisão antes do piloto

Antes da homologação, revisar conjuntamente licenças do servidor, SDK, imagens de contêiner, bibliotecas do frontend, fontes, ícones, emojis e qualquer ativo distribuído.
