'use strict';

class AuditLogRepository {
  constructor(db) {
    this.db = db;
  }

  record(action) {
    this.db
      .prepare("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))")
      .run(action);
  }
}

module.exports = AuditLogRepository;
