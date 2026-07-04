# Changelog

## 0.1.0 - Kh鬨ｾ・ｶ繝ｻ・ｻ髫ｹ・ｿ郢晢ｽｻt鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・｡o

- T鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・｡o repo Python cho Nakazasen AI Router.
- Th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪm API router t鬨ｾ・ｶ繝ｻ・ｻ鬮ｫ・ｪ繝ｻ・ｴ thi鬨ｾ・ｶ繝ｻ・ｻ驛｢譏ｴ繝ｻ
- Th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪm provider gi鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・｣ l鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｭp cho success, quota fail, auth fail, timeout.
- Th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪm test fallback, cooldown quota, disable auth, local_only, v郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰ kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng log API key.

## 0.3.0 - Provider Registry v郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰ env config

- Th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪm Provider Registry cho OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral v郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰ local OpenAI-compatible.
- Th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪm `create_router_from_env()` 郢晢ｽｻ郢晢ｽｻ繝ｻ・ｻ陝ｷ・｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻt鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・｡o router t鬨ｾ・ｶ繝ｻ・ｻ郢晢ｽｻ繝ｻ・ｫ bi鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｿn m郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴi tr郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｰ鬨ｾ・ｶ繝ｻ・ｻ髫ｲ・｡繝ｻ・ｵg.
- Cloud provider kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng c郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｳ API key s鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｽ b鬨ｾ・ｶ繝ｻ・ｻ驛｢譎｢・ｽ・ｻb鬨ｾ・ｶ繝ｻ・ｻ驛｢譎｢・ｽ・ｻqua.
- Local OpenAI-compatible c郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｳ th鬨ｾ・ｶ繝ｻ・ｻ驛｢譎｢・ｽ・ｻch鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・｡y kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng c鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｧn key n鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｿu d郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｹng localhost/127.0.0.1.
- Test m鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｷc 郢晢ｽｻ郢晢ｽｻ繝ｻ・ｻ陝ｷ・｢繝ｻ・ｽ繝ｻ・ｻ髫ｴ螟ｲ・ｽ・ｵh v鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｫn mock-first, kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng g鬨ｾ・ｶ繝ｻ・ｻ鬩搾ｽｨ郢晢ｽｻinternet v郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰ kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng c鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｧn API key th鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｭt.

## 0.4.0 - Optional network transport v郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰ live smoke test

- Th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪm `UrllibHTTPClient` d郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｹng Python standard library 郢晢ｽｻ郢晢ｽｻ繝ｻ・ｻ陝ｷ・｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻg鬨ｾ・ｶ繝ｻ・ｻ鬩搾ｽｨ郢晢ｽｻprovider th鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｭt khi caller opt-in.
- `create_router_from_env(enable_network=True)` m鬨ｾ・ｶ繝ｻ・ｻ髯橸ｽｫ郢晢ｽｻd郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｹng transport th鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｭt; m鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｷc 郢晢ｽｻ郢晢ｽｻ繝ｻ・ｻ陝ｷ・｢繝ｻ・ｽ繝ｻ・ｻ髫ｴ螟ｲ・ｽ・ｵh v鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｫn kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng g鬨ｾ・ｶ繝ｻ・ｻ鬩搾ｽｨ郢晢ｽｻinternet.
- Th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪm live smoke test t郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｹy ch鬨ｾ・ｶ繝ｻ・ｻ鬮｢・ｧ繝ｻ・ｱ, skip m鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｷc 郢晢ｽｻ郢晢ｽｻ繝ｻ・ｻ陝ｷ・｢繝ｻ・ｽ繝ｻ・ｻ髫ｴ螟ｲ・ｽ・ｵh n鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｿu kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng c郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｳ `RUN_LIVE_AI_TESTS=1`.
- Kh郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｴng y郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪu c鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｧu API key th鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｭt cho test m鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｷc 郢晢ｽｻ郢晢ｽｻ繝ｻ・ｻ陝ｷ・｢繝ｻ・ｽ繝ｻ・ｻ髫ｴ螟ｲ・ｽ・ｵh.

## 0.1.0 - Internal release preparation

- Th繝ｻ繝ｻ・ｽ・ｪm script live smoke an to繝ｻ繝ｻ・｣・ｰn 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ郢晢ｽｻki騾ｶ・ｻ郢昴・tra provider th髯ゑｽｯ繝ｻ・ｭt b髯ゑｽｯ繝ｻ・ｱng key n髯ゑｽｯ繝ｻ・ｱm ngo繝ｻ繝ｻ・｣・ｰi repo.
- X繝ｻ繝ｻ・ｽ・｡c minh lu騾ｶ・ｻ雋ゑｽ｡g g騾ｶ・ｻ驍ｨ繝ｻth髯ゑｽｯ繝ｻ・ｭt c繝ｻ繝ｻ・ｽ・ｳ ki騾ｶ・ｻ郢昴・so繝ｻ繝ｻ・ｽ・｡t qua transport opt-in.
- Chu髯ゑｽｯ繝ｻ・ｩn b騾ｶ・ｻ郢晢ｽｻtag n騾ｶ・ｻ陷繝ｻb騾ｶ・ｻ郢晢ｽｻ`v0.1.0` sau khi unit test, packaging, secret scan v繝ｻ繝ｻ・｣・ｰ live smoke pass.

## Gate 7 - Live provider strategy stabilization

- Th・・ｽｪm strategy `live_free_first` v逶ｻ螫・th逶ｻ・ｩ t逶ｻ・ｱ: DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral, OpenRouter, Groq.
- Th・・ｽｪm `create_live_free_first_router_from_env()` l・・｣ｰm wrapper ti逶ｻ繻ｻ d逶ｻ・･ng.
- C陂ｯ・ｭp nh陂ｯ・ｭt live smoke script h逶ｻ繝ｻtr逶ｻ・｣ `--provider all` v・・｣ｰ `--stop-on-first-pass`.
- Live smoke b・・ｽ｡o l逶ｻ謫・an to・・｣ｰn h・・ｽ｡n: `error_type`, `status_code`, model v・・｣ｰ message ・・ｦ･・｣ r・・ｽｺt g逶ｻ閧ｱ/sanitize.
- Gi逶ｻ・ｯ m陂ｯ・ｷc ・・ｻ幢ｽｻ譚ｵh kh・・ｽｴng g逶ｻ邨・internet n陂ｯ・ｿu ch・・ｽｰa opt-in `enable_network=True`.

## Gate 8 - Gemini provider support

- Thﾃｪm provider `gemini` vﾃo registry qua endpoint OpenAI-compatible c盻ｧa Gemini API.
- Thﾃｪm `GEMINI_API_KEY` vﾃo live smoke script vﾃ h盻・tr盻｣ nhi盻「 format key-file an toﾃn.
- ﾄ脆ｰa Gemini lﾃｪn ﾄ黛ｺｧu strategy `live_free_first`.
- Thﾃｪm test registry/env/url/strategy/live-smoke parser cho Gemini.
