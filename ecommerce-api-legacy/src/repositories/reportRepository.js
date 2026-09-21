'use strict';

// Single JOIN query replaces the N+1 loop of the legacy financial report.
class ReportRepository {
  constructor(db) {
    this.db = db;
  }

  financialRows() {
    return this.db
      .prepare(
        `SELECT c.id        AS course_id,
                c.title     AS course_title,
                u.name      AS student_name,
                p.amount    AS payment_amount,
                p.status    AS payment_status
         FROM courses c
         LEFT JOIN enrollments e ON e.course_id = c.id
         LEFT JOIN users u       ON u.id = e.user_id
         LEFT JOIN payments p    ON p.enrollment_id = e.id
         ORDER BY c.id`
      )
      .all();
  }
}

module.exports = ReportRepository;
