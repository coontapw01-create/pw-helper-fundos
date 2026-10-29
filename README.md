# Fundos da mini-janela do PW Helper

Este repositório é o "site" dos fundos. O PW Helper lê o `catalog.json` daqui e mostra os fundos em
**Skins › Fundos da mini-janela**. Quando você envia um WEBP novo, o GitHub gera sozinho o catálogo e a
miniatura (cerca de 1 minuto), e o PW Helper mostra o fundo novo na próxima conferência (ao abrir o app,
a cada 30 minutos, ou no botão **Atualizar**).

## Adicionar um fundo
1. Abra a pasta `fundos/` do repositório no GitHub › **Add file › Upload files**.
2. Arraste o `.webp` (no envio pelo site o limite é 25 MB por arquivo; pelo Git, 100 MB).
3. **Commit changes**. Pronto.

Nome, autor e tags são opcionais, em `fundos.json`:
```json
{ "sakura-a-noite": { "name": "Sakura à noite", "author": "Seu nome", "tags": ["japão", "noite"] } }
```
A chave é o nome do arquivo em minúsculas, sem acento e com hífens (ex.: `Sakura à noite.webp` → `sakura-a-noite`).

## Trocar ou remover
- Trocar: envie um arquivo com o mesmo nome; o PW Helper baixa a versão nova sozinho.
- Remover: apague o arquivo de `fundos/`; ele some da lista e do cache do PW Helper.

## Página de galeria (opcional)
Settings › Pages › Branch `main` / `(root)`. A galeria fica em `https://coontapw01-create.github.io/pw-helper-fundos/`.

## Endereço para o PW Helper
`https://raw.githubusercontent.com/coontapw01-create/pw-helper-fundos/main/catalog.json`
