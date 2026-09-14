# Playbook de Marketing - Instagram MCP (@positivamenteclinicaesp)

Guia para usar o Claude como analista/estrategista de marketing sobre o Instagram da
POSITIVAMENTE via o MCP `instagram`. Aponte o Claude para este arquivo no inicio de cada rotina.

Conta: POSITIVAMENTE - Clinica de Especialidades (Psicologia, Nutricao) | Lavras/MG + Online
Baseline (14/09/2026): 2305 seguidores, 929 seguindo, 588 posts.

## 1. O que da pra LER (fontes de dado confirmadas ao vivo)

### Perfil
- followers_count, follows_count, media_count, nome, bio, site, @.

### Insights de CONTA (get_account_insights) - por dia/semana/28 dias
- reach, profile_views
- accounts_engaged, total_interactions
- likes, comments, saves, shares, replies
- follows_and_unfollows (crescimento liquido)

### Demografia de seguidores (follower_demographics)
- por cidade, idade, genero, pais.

### Insights por POST (get_media_insights, feed)
- reach, likes, comments, saved, shares, total_interactions
- profile_visits (quantos visitaram o perfil a partir do post)
- follows (quantos seguiram a partir do post)  <- metrica de conversao

### Insights por REEL
- tudo do feed +: views, ig_reels_avg_watch_time, ig_reels_video_view_total_time (retencao)

### Outros
- get_media_posts: lista posts (id, tipo, legenda, permalink, timestamp)
- get_comments: comentarios de um post
- get_stories: stories ativos
- search_hashtag + get_hashtag_media: pesquisa de hashtag (top/recent)
- business_discovery: perfil publico de concorrentes (seguidores, posts, bio) -> benchmarking
- get_content_publishing_limit: quota de publicacao (100 posts/24h)

## 2. O que da pra FAZER (escrita - sempre com aprovacao humana)
- publish_media (foto), publish_reel, publish_carousel
- post_comment, reply_to_comment, hide_comment, delete_comment

REGRA: toda acao de escrita e PUBLICA e irreversivel. Claude propoe, humano aprova, dai executa.

## 3. Bloqueado (precisa App Review da Meta, nao e limitacao de codigo)
- send_dm / get_conversations (DMs) -> permissao instagram_manage_messages
- get_mentions -> permissao + webhook

## 4. Limitacao importante: historico
A Graph API entrega janelas curtas/pontuais. Para ter TENDENCIA (crescimento semana a semana,
evolucao de reach), e preciso TIRAR SNAPSHOTS periodicos e guardar. Sem isso, cada consulta e so
uma foto do momento. Solucao: logger que roda diario/semanal e acumula em CSV/sqlite local.

## 5. Rotinas prontas (o que pedir ao Claude)

### R1. Relatorio semanal de performance
reach/engajamento/saves/shares da semana vs semana anterior; crescimento liquido de seguidores;
top 3 e bottom 3 posts por reach e por follows; feed vs reels; 3 recomendacoes acionaveis.

### R2. Analise de conversao de conteudo
Ranking de posts por `follows` e por `profile_visits`. Descobrir QUE formato/tema/gancho traz
seguidor, nao so like. Saida: "faca mais X, menos Y".

### R3. Retencao de Reels
avg_watch_time e video_view_total_time por reel; quais prendem ate o fim; padroes de gancho.

### R4. Demografia -> decisao de conteudo
Onde estao os seguidores (cidade/idade/genero) vs publico-alvo da clinica (Lavras/MG + online).
Ajustar horario, lingua, tema.

### R5. Benchmarking de concorrentes
Lista de @ concorrentes -> business_discovery -> comparar seguidores/frequencia/temas.
Rodar mensal para ver quem cresce.

### R6. Pesquisa de hashtag
search_hashtag + get_hashtag_media para achar hashtags ativas no nicho (psicologia, nutricao,
saude mental, Lavras) e ver o que engaja.

### R7. Community management
get_comments -> triagem (duvida, elogio, lead, spam) -> sugerir respostas -> aprovar -> responder.
Esconder/apagar spam com aprovacao.

### R8. Calendario + publicacao
Planejar posts, redigir legendas, e (com aprovacao) publicar via publish_*.

## 6. Metricas-chave a acompanhar (KPIs)
- Alcance (reach) e alcance de nao-seguidores (descoberta).
- Taxa de engajamento = total_interactions / reach.
- Saves e Shares (sinal forte de valor/algoritmo).
- Conversao de perfil: profile_visits e follows por post.
- Crescimento liquido de seguidores (follows_and_unfollows).
- Retencao de reels (watch time).

## 7. Cadencia sugerida
- Diario: snapshot de metricas (logger) + triagem de comentarios.
- Semanal: R1 + R2.
- Mensal: R3 + R4 + R5 + revisao de estrategia.

## 8. Comandos de operacao
- Rodar server/registrar: ver README + run.sh (MCP `instagram` ja registrado em escopo user).
- Renovar token (se um dia expirar): ./refresh_token.sh
- Diagnostico das tools: .venv/bin/python test_tools.py
