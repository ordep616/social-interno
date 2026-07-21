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
