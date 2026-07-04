# Ki蘯ｿn trﾃｺc Nakazasen AI Router

## M盻･c tiﾃｪu d盻・hi盻ブ

Router gi盻創g nhﾆｰ ngﾆｰ盻拱 ﾄ訴盻「 ph盻訴. Khi app c蘯ｧn g盻絞 AI, router ch盻肱 provider phﾃｹ h盻｣p. N蘯ｿu provider ﾄ黛ｺｧu tiﾃｪn l盻擁, router th盻ｭ provider ti蘯ｿp theo theo chﾃｭnh sﾃ｡ch ﾄ妥｣ ﾄ黛ｺｷt.

## Thﾃnh ph蘯ｧn chﾃｭnh

- `AIRequest`: yﾃｪu c蘯ｧu ﾄ黛ｺｧu vﾃo, vﾃｭ d盻･ prompt vﾃ metadata.
- `AIResult`: k蘯ｿt qu蘯｣ tr蘯｣ v盻・t盻ｫ provider ﾄ柁ｰ盻｣c ch盻肱.
- `ProviderBase`: l盻孅 n盻］ cho m盻絞 provider.
- `ProviderCandidate`: thﾃｴng tin provider trong danh sﾃ｡ch l盻ｱa ch盻肱.
- `ProviderHealth`: tr蘯｡ng thﾃ｡i provider: ﾄ疎ng b蘯ｭt, cooldown ﾄ黛ｺｿn khi nﾃo, l盻擁 g蘯ｧn nh蘯･t.
- `RouterPolicy`: chﾃｭnh sﾃ｡ch router, vﾃｭ d盻･ `local_only`.
- `AIRouter`: b盻・ﾄ訴盻「 ph盻訴 chﾃｭnh.

## Lu盻渡g x盻ｭ lﾃｽ

1. App t蘯｡o `AIRequest`.
2. `AIRouter` l盻皇 provider khﾃｴng h盻｣p l盻・
   - Provider b盻・disable.
   - Provider ﾄ疎ng cooldown.
   - Provider cloud khi `local_only=True`.
3. Router g盻絞 provider theo th盻ｩ t盻ｱ ﾆｰu tiﾃｪn.
4. N蘯ｿu provider quota l盻擁, router ﾄ柁ｰa provider vﾃo cooldown.
5. N蘯ｿu provider auth l盻擁, router disable provider.
6. N蘯ｿu cﾃｲn provider khﾃ｡c, router fallback.
7. N蘯ｿu khﾃｴng provider nﾃo thﾃnh cﾃｴng, router bﾃ｡o l盻擁 t盻貧g h盻｣p.

## B蘯｣o m蘯ｭt

- Khﾃｴng cﾃｳ provider th蘯ｭt trong giai ﾄ双蘯｡n nﾃy.
- Khﾃｴng cﾃｳ API key th蘯ｭt trong repo.
- Log request s蘯ｽ che cﾃ｡c trﾆｰ盻拵g nh蘯｡y c蘯｣m nhﾆｰ `api_key`, `token`, `secret`, `authorization`.

## Provider Registry

Provider Registry lﾃ danh sﾃ｡ch c蘯･u hﾃｬnh t盻訴 thi盻ブ cho cﾃ｡c provider OpenAI-compatible ph盻・bi蘯ｿn. Registry khﾃｴng ch盻ｩa API key th蘯ｭt. Nﾃｳ ch盻・bi蘯ｿt:

- tﾃｪn provider;
- base URL m蘯ｷc ﾄ黛ｻ杵h;
- tﾃｪn bi蘯ｿn mﾃｴi trﾆｰ盻拵g ch盻ｩa API key;
- model m蘯ｷc ﾄ黛ｻ杵h;
- provider lﾃ cloud hay local;
- ghi chﾃｺ ng蘯ｯn ﾄ黛ｻ・ngﾆｰ盻拱 dﾃｹng hi盻ブ provider dﾃｹng cho vi盻㌘ gﾃｬ.

Hﾃm `create_router_from_env()` ﾄ黛ｻ皇 key t盻ｫ bi蘯ｿn mﾃｴi trﾆｰ盻拵g, b盻・qua cloud provider khﾃｴng cﾃｳ key, vﾃ cho phﾃｩp local OpenAI-compatible ch蘯｡y khﾃｴng c蘯ｧn key n蘯ｿu base URL lﾃ localhost/127.0.0.1. Test cﾃｳ th盻・inject `http_client_factory` ﾄ黛ｻ・khﾃｴng g盻絞 internet.

## Transport layer

Transport layer tﾃ｡ch vi盻㌘ g盻絞 HTTP kh盻淑 provider adapter. `OpenAICompatibleProvider` ch盻・ph盻･ thu盻冂 interface `post(url, headers, json, timeout)`, nﾃｪn unit test cﾃｳ th盻・inject mock client vﾃ khﾃｴng g盻絞 internet.

`UrllibHTTPClient` lﾃ transport th蘯ｭt d盻ｱa trﾃｪn Python standard library. Nﾃｳ ch盻・ﾄ柁ｰ盻｣c dﾃｹng khi caller truy盻］ `enable_network=True` ho蘯ｷc truy盻］ explicit `http_client_factory`. M蘯ｷc ﾄ黛ｻ杵h `create_router_from_env()` dﾃｹng `NoNetworkHTTPClient` ﾄ黛ｻ・trﾃ｡nh network I/O ngoﾃi ﾃｽ mu盻創.
