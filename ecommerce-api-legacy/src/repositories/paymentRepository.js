'use strict';

class PaymentRepository {
  constructor(db) {
    this.db = db;
  }

  create(enrollmentId, amount, status) {
    const info = this.db
      .prepare('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)')
      .run(enrollmentId, amount, status);
    return info.lastInsertRowid;
  }
}

module.exports = PaymentRepository;
