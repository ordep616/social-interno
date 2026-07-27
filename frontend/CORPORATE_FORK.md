# Fork corporativo do Cinny

Esta pasta contém uma cópia do Cinny `v4.12.3`, obtida do repositório oficial
`https://github.com/cinnyapp/cinny` no commit
`69515e8e81d082a7b0609247e296391d3d6f1e38`.

## Licença

O código original e as modificações são mantidos sob AGPL-3.0-only. O arquivo
`LICENSE` e os avisos de autoria devem ser preservados. Consulte também
`../docs/OPEN_SOURCE.md`.

## Objetivo das alterações

- restringir o cliente ao homeserver corporativo;
- remover cadastro, seleção de servidores e descoberta pública;
- integrar o fluxo OIDC definido pela plataforma;
- aplicar nome, textos e ativos próprios;
- manter somente recursos aprovados para o MVP.

## Regra de manutenção

Evite alterações profundas no núcleo Matrix. Cada modificação corporativa deve
ser pequena e rastreável para facilitar a comparação e a atualização a partir
de novas versões oficiais.

## Procedimento de atualização do fork

O fork foi incorporado sem o histórico Git externo do Cinny. Por isso, toda
atualização deve partir de uma cópia limpa do upstream, comparar as mudanças
oficiais com as personalizações corporativas e registrar a nova origem antes
de entregar a alteração.

### Antes de começar

1. Trabalhe em uma branch específica, nunca diretamente na `main`.
2. Leia `../docs/PROJECT.md`, `../docs/ARCHITECTURE.md`,
   `../docs/TASKS.md`, `../docs/DECISIONS.md`, `../docs/API.md`,
   `../docs/OPEN_SOURCE.md`, `AGENTS.md` e este arquivo.
3. Confirme em `../docs/DECISIONS.md` e `../docs/TASKS.md` se a nova versão do
   Cinny, do Matrix e do `matrix-js-sdk` já foi aprovada pelos dois
   colaboradores. Mudança de versão do SDK ou recurso compartilhado exige
   alinhamento conjunto antes do merge.
4. Verifique a árvore de trabalho com `git status --short --branch` e não
   reverta alterações de outra pessoa.
5. Anote a versão atual do fork registrada neste arquivo e em
   `../docs/OPEN_SOURCE.md`.

### Preparar a referência upstream

1. Escolha a tag ou commit candidato no repositório oficial
   `https://github.com/cinnyapp/cinny`.
2. Em uma pasta temporária fora de `frontend/`, obtenha uma cópia limpa da
   versão atual registrada e outra da versão candidata.
3. Registre o hash exato da versão candidata com `git rev-parse HEAD`.
4. Leia `LICENSE`, notas de versão, `package.json`, lockfile e mudanças em
   dependências, assets e configuração.
5. Se houver nova dependência, fonte, ícone, imagem, som ou código externo,
   atualize `../docs/OPEN_SOURCE.md` antes da revisão.

### Comparar e portar

1. Gere um diff entre a versão upstream atual registrada e a versão candidata.
2. Gere outro diff entre a versão upstream atual registrada e este fork
   corporativo.
3. Porte a versão candidata para `frontend/` mantendo as personalizações
   corporativas pequenas e explícitas.
4. Preserve obrigatoriamente:
   - `LICENSE`, avisos de autoria e obrigações da AGPL-3.0-only;
   - `AGENTS.md`, este `CORPORATE_FORK.md` e a rastreabilidade em
     `../docs/OPEN_SOURCE.md`;
   - restrição ao homeserver configurado;
   - remoção de cadastro público, seleção de homeserver e descoberta pública;
   - rota corporativa `/activate` conforme `DEC-022`;
   - painel administrativo fechado por padrão e condicionado a
     `GET /v1/me/capabilities`;
   - marca e ativos próprios já aprovados ou registrados como provisórios;
   - ausência de Telegram, MTProto, GramJS, TDLib, `api_id` e `api_hash`.
5. Não copie código do Element Web, Telegram Web ou outro projeto apenas por
   semelhança visual. Qualquer incorporação nova exige registro de origem,
   commit, arquivos, licença e aprovação.

### Validar

1. Reinstale dependências somente quando o lockfile ou `package.json` mudar.
2. Execute as verificações aplicáveis:
   - `npm run build`;
   - `npm run lint`;
   - `npm run typecheck`.
3. Se uma verificação falhar por problema herdado do upstream, registre o erro
   separadamente da regressão introduzida pelo fork.
4. Teste manualmente contra um homeserver Matrix de desenvolvimento:
   - login, restauração de sessão e logout;
   - bloqueio de homeserver externo;
   - ausência de cadastro público, seletor de homeserver e descoberta pública;
   - `/activate#token` removendo o fragmento da URL e mantendo o token só em
     memória;
   - administração oculta sem capacidade e aberta somente com capacidade
     positiva;
   - lista de salas, conversa, envio, mídia, mensagens de voz, responsividade e
     PWA.
5. Quando `matrix-js-sdk`, convenções Matrix ou recursos compartilhados mudarem,
   combine validação com o Colaborador 1 no marco de integração apropriado.

### Finalizar

1. Atualize este arquivo com a nova versão, commit de origem e observações
   relevantes.
2. Atualize `../docs/OPEN_SOURCE.md` com versões, commits, licenças,
   dependências e ativos alterados.
3. Atualize `../docs/TASKS.md`, `../docs/DECISIONS.md` ou `../docs/API.md`
   quando a atualização mudar escopo, contrato, decisão ou critério de aceite.
4. Confirme que não há segredos, credenciais, tokens ou dados pessoais
   indevidos no repositório.
5. Entregue a alteração para revisão do outro colaborador com:
   - versão anterior e versão nova;
   - commit upstream exato;
   - resumo das personalizações reaplicadas;
   - validações executadas e falhas herdadas conhecidas.
