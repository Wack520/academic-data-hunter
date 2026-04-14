(() => {
  const define = (obj, key, getter) => {
    try {
      Object.defineProperty(obj, key, {
        get: getter,
        configurable: true
      });
    } catch (_) {}
  };

  const seed = (Date.now() % 7) + 1;
  const fakeCores = [4, 6, 8][seed % 3];
  const fakeMem = [4, 8, 16][seed % 3];

  define(navigator, "webdriver", () => false);
  define(navigator, "hardwareConcurrency", () => fakeCores);
  define(navigator, "deviceMemory", () => fakeMem);
  define(navigator, "platform", () => "Win32");
  define(navigator, "language", () => "zh-CN");
  define(navigator, "languages", () => ["zh-CN", "zh", "en-US"]);
})();
