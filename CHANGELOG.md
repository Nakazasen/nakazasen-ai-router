# Changelog

## 0.1.0 - Kh鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬮ｫ・ｹ繝ｻ・ｿ驛｢譎｢・ｽ・ｻt鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｡o

- T鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｡o repo Python cho Nakazasen AI Router.
- Th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪm API router t鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬯ｮ・ｫ繝ｻ・ｪ郢晢ｽｻ繝ｻ・ｴ thi鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴擾ｽｴ郢晢ｽｻ
- Th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪm provider gi鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣ l鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｭp cho success, quota fail, auth fail, timeout.
- Th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪm test fallback, cooldown quota, disable auth, local_only, v驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣郢晢ｽｻ繝ｻ・ｰ kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng log API key.

## 0.3.0 - Provider Registry v驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣郢晢ｽｻ繝ｻ・ｰ env config

- Th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪm Provider Registry cho OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral v驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣郢晢ｽｻ繝ｻ・ｰ local OpenAI-compatible.
- Th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪm `create_router_from_env()` 驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻt鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｡o router t鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｫ bi鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｿn m驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴi tr驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｰ鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬮ｫ・ｲ繝ｻ・｡郢晢ｽｻ繝ｻ・ｵg.
- Cloud provider kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng c驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｳ API key s鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ b鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻb鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻqua.
- Local OpenAI-compatible c驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｳ th鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻch鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｡y kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng c鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧn key n鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｿu d驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｹng localhost/127.0.0.1.
- Test m鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｷc 驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬮ｫ・ｴ陞滂ｽｲ繝ｻ・ｽ繝ｻ・ｵh v鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｫn mock-first, kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng g鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬯ｩ謳ｾ・ｽ・ｨ驛｢譎｢・ｽ・ｻinternet v驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣郢晢ｽｻ繝ｻ・ｰ kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng c鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧn API key th鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｭt.

## 0.4.0 - Optional network transport v驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣郢晢ｽｻ繝ｻ・ｰ live smoke test

- Th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪm `UrllibHTTPClient` d驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｹng Python standard library 驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻg鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬯ｩ謳ｾ・ｽ・ｨ驛｢譎｢・ｽ・ｻprovider th鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｭt khi caller opt-in.
- `create_router_from_env(enable_network=True)` m鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬮ｯ讖ｸ・ｽ・ｫ驛｢譎｢・ｽ・ｻd驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｹng transport th鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｭt; m鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｷc 驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬮ｫ・ｴ陞滂ｽｲ繝ｻ・ｽ繝ｻ・ｵh v鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｫn kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng g鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬯ｩ謳ｾ・ｽ・ｨ驛｢譎｢・ｽ・ｻinternet.
- Th驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪm live smoke test t驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｹy ch鬯ｨ・ｾ繝ｻ・ｶ郢晢ｽｻ繝ｻ・ｻ鬯ｮ・｢繝ｻ・ｧ郢晢ｽｻ繝ｻ・ｱ, skip m鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｷc 驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬮ｫ・ｴ陞滂ｽｲ繝ｻ・ｽ繝ｻ・ｵh n鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｿu kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng c驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｳ `RUN_LIVE_AI_TESTS=1`.
- Kh驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴng y驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｪu c鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧu API key th鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｭt cho test m鬯ｮ・ｯ郢ｧ謇假ｽｽ・ｽ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｷc 驛｢譎｢・ｽ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬮ｫ・ｴ陞滂ｽｲ繝ｻ・ｽ繝ｻ・ｵh.

## 0.1.0 - Internal release preparation

- Th郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｪm script live smoke an to郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰn 郢晢ｽｻ郢晢ｽｻ繝ｻ・ｻ陝ｷ・｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻki鬨ｾ・ｶ繝ｻ・ｻ驛｢譏ｴ繝ｻtra provider th鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｭt b鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｱng key n鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｱm ngo郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰi repo.
- X郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・｡c minh lu鬨ｾ・ｶ繝ｻ・ｻ髮九ｑ・ｽ・｡g g鬨ｾ・ｶ繝ｻ・ｻ鬩搾ｽｨ郢晢ｽｻth鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｭt c郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｳ ki鬨ｾ・ｶ繝ｻ・ｻ驛｢譏ｴ繝ｻso郢晢ｽｻ郢晢ｽｻ繝ｻ・ｽ繝ｻ・｡t qua transport opt-in.
- Chu鬮ｯ繧托ｽｽ・ｯ郢晢ｽｻ繝ｻ・ｩn b鬨ｾ・ｶ繝ｻ・ｻ驛｢譎｢・ｽ・ｻtag n鬨ｾ・ｶ繝ｻ・ｻ髯ｷﾂ郢晢ｽｻb鬨ｾ・ｶ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ`v0.1.0` sau khi unit test, packaging, secret scan v郢晢ｽｻ郢晢ｽｻ繝ｻ・｣繝ｻ・ｰ live smoke pass.

## Gate 7 - Live provider strategy stabilization

- Th繝ｻ繝ｻ・ｽ・ｪm strategy `live_free_first` v騾ｶ・ｻ陞ｫ繝ｻth騾ｶ・ｻ繝ｻ・ｩ t騾ｶ・ｻ繝ｻ・ｱ: DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral, OpenRouter, Groq.
- Th繝ｻ繝ｻ・ｽ・ｪm `create_live_free_first_router_from_env()` l繝ｻ繝ｻ・｣・ｰm wrapper ti騾ｶ・ｻ郢ｻ・ｻ d騾ｶ・ｻ繝ｻ・･ng.
- C髯ゑｽｯ繝ｻ・ｭp nh髯ゑｽｯ繝ｻ・ｭt live smoke script h騾ｶ・ｻ郢晢ｽｻtr騾ｶ・ｻ繝ｻ・｣ `--provider all` v繝ｻ繝ｻ・｣・ｰ `--stop-on-first-pass`.
- Live smoke b繝ｻ繝ｻ・ｽ・｡o l騾ｶ・ｻ隰ｫ繝ｻan to繝ｻ繝ｻ・｣・ｰn h繝ｻ繝ｻ・ｽ・｡n: `error_type`, `status_code`, model v繝ｻ繝ｻ・｣・ｰ message 繝ｻ繝ｻ・ｦ・･繝ｻ・｣ r繝ｻ繝ｻ・ｽ・ｺt g騾ｶ・ｻ髢ｧ・ｱ/sanitize.
- Gi騾ｶ・ｻ繝ｻ・ｯ m髯ゑｽｯ繝ｻ・ｷc 繝ｻ繝ｻ・ｻ蟷｢・ｽ・ｻ隴夲ｽｵh kh繝ｻ繝ｻ・ｽ・ｴng g騾ｶ・ｻ驍ｨ繝ｻinternet n髯ゑｽｯ繝ｻ・ｿu ch繝ｻ繝ｻ・ｽ・ｰa opt-in `enable_network=True`.

## Gate 8 - Gemini provider support

- Th・・ｽｪm provider `gemini` v・・｣ｰo registry qua endpoint OpenAI-compatible c逶ｻ・ｧa Gemini API.
- Th・・ｽｪm `GEMINI_API_KEY` v・・｣ｰo live smoke script v・・｣ｰ h逶ｻ繝ｻtr逶ｻ・｣ nhi逶ｻ縲・format key-file an to・・｣ｰn.
- ・・ф・ｰa Gemini l・・ｽｪn ・・ｻ幢ｽｺ・ｧu strategy `live_free_first`.
- Th・・ｽｪm test registry/env/url/strategy/live-smoke parser cho Gemini.

## Gate 9 - Gemini model catalog and model-level live smoke

- M盻・r盻冢g catalog model cho provider `gemini` g盻杜 Gemini 3.x/2.5, Gemma 4/3/3n vﾃ Robotics-ER preview.
- Thﾃｪm `--model`, `--list-models`, `--test-all-models` cho live smoke script.
- Thﾃｪm unit test cho model catalog, model override, list/test-all model flow b蘯ｱng mock.
- Live smoke model-level gi盻ｯ output an toﾃn: khﾃｴng in key, prompt, Authorization header ho蘯ｷc raw response dﾃi.
