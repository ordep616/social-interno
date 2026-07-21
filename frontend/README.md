# Frontend corporativo

Cliente web Matrix baseado no Cinny `v4.12.3`.

## Desenvolvimento local

```bash
npm ci
npm start
```

O cliente usa inicialmente `http://localhost:8008`, definido em `config.json`.
O homeserver é fixo na configuração e não possui seletor na interface. Antes
de homologação, esse endereço deverá ser substituído pelo domínio HTTPS aprovado.

## Limites atuais

- cadastro público não possui rota ou link na interface;
- descoberta de salas públicas não aparece na navegação;
- servidores externos foram removidos da configuração;
- OIDC, nome definitivo e identidade visual ainda estão pendentes;
- a configuração do Synapse continua pertencendo ao Colaborador 1.

Consulte `CORPORATE_FORK.md` para origem, licença e regra de manutenção.
