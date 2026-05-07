let BackendDatabase;
let sqliteBackendName;

try {
  const mod = await import("better-sqlite3");
  BackendDatabase = mod.default;
  sqliteBackendName = "better-sqlite3";
} catch (error) {
  if (error.code !== "ERR_MODULE_NOT_FOUND") {
    throw error;
  }

  const { DatabaseSync } = await import("node:sqlite");
  BackendDatabase = DatabaseSync;
  sqliteBackendName = "node:sqlite";
}

export const sqliteBackend = sqliteBackendName;

export default class Database {
  constructor(path, options = {}) {
    this._db = new BackendDatabase(path, options);
    return new Proxy(this, {
      get(target, prop, receiver) {
        if (prop === 'constructor') return Database;
        return prop in target ? Reflect.get(target, prop, receiver) : Reflect.get(target._db, prop, target._db);
      }
    });
  }
}
