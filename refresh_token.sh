#!/usr/bin/env bash
# Renova o long-lived access token da Meta (estende +60 dias) e atualiza o .env.
# Uso: ./refresh_token.sh   (roda de qualquer cwd)
# Nao imprime o token. Faz backup do .env em .env.bak antes de mexer.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then echo "ERRO: .env nao encontrado em $(pwd)" >&2; exit 1; fi
set -a; . ./.env; set +a

: "${FACEBOOK_APP_ID:?FACEBOOK_APP_ID faltando no .env}"
: "${FACEBOOK_APP_SECRET:?FACEBOOK_APP_SECRET faltando no .env}"
: "${INSTAGRAM_ACCESS_TOKEN:?INSTAGRAM_ACCESS_TOKEN faltando no .env}"
API="${INSTAGRAM_API_VERSION:-v19.0}"

echo "Trocando token atual por um novo long-lived..."
resp="$(curl -s "https://graph.facebook.com/${API}/oauth/access_token" \
  --get \
  --data-urlencode "grant_type=fb_exchange_token" \
  --data-urlencode "client_id=${FACEBOOK_APP_ID}" \
  --data-urlencode "client_secret=${FACEBOOK_APP_SECRET}" \
  --data-urlencode "fb_exchange_token=${INSTAGRAM_ACCESS_TOKEN}")"

new_token="$(printf '%s' "$resp" | python3 -c "import sys,json
d=json.load(sys.stdin)
if 'access_token' not in d:
    sys.exit('ERRO Meta: '+json.dumps(d.get('error',d)))
print(d['access_token'])")"

# backup e substituicao segura (delimitador | evita colisao com / do token)
cp .env .env.bak
python3 - "$new_token" <<'PY'
import sys,re,io
tok=sys.argv[1]
p='.env'
lines=open(p,encoding='utf-8').read().splitlines()
out=[]; done=False
for l in lines:
    if l.startswith('INSTAGRAM_ACCESS_TOKEN='):
        out.append('INSTAGRAM_ACCESS_TOKEN='+tok); done=True
    else:
        out.append(l)
if not done: out.append('INSTAGRAM_ACCESS_TOKEN='+tok)
open(p,'w',encoding='utf-8').write('\n'.join(out)+'\n')
PY

# valida e mostra nova expiracao (sem imprimir token)
info="$(curl -s "https://graph.facebook.com/${API}/debug_token?input_token=${new_token}&access_token=${new_token}")"
printf '%s' "$info" | python3 -c "import sys,json,datetime
d=json.load(sys.stdin).get('data',{})
ea=d.get('expires_at',0)
if ea==0: print('OK. Novo token valido. Expira: NUNCA')
else:
    dt=datetime.datetime.fromtimestamp(ea,datetime.timezone.utc)
    print('OK. Novo token valido. Expira em', dt.isoformat())
print('Backup do .env anterior: .env.bak')
print('Reinicie o Claude Code (ou /mcp) para o server pegar o token novo.')"
