```sh
git clone https://github.com/elizaos/eliza.git  # We use v0.25.9
```
```sh
cp .env.example .env  ## Fill in the appropriate values.

# Telegram Configuration
# TELEGRAM_BOT_TOKEN=

# OpenRouter Configuration
# OPENROUTER_API_KEY=sk-or-v1-\*...\* 
# OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324:free
```

### Storacha Configuration
```sh
npm i -g @web3-storage/w3cli
w3 login # use github
w3 space create claudia-agent
w3 key create
w3 delegation create [pk] --can 'store/add' --can 'filecoin/offer' --can 'upload/add' --can 'space/blob/add' --can 'space/index/add' | base64

# did:key:**....** (pk)

# Storacha Configuration in .env (eliza)
# STORACHA_AGENT_PRIVATE_KEY=
# STORACHA_AGENT_DELEGATION= (include base64 in quotes)

npx elizaos plugins add @elizaos-plugins/plugin-storacha

# plugins: ["@elizaos-plugins/plugin-storacha"],
```

```sh
pnpm i
pnpm build
pnpm start --characters="characters/claudia_en.json"
```