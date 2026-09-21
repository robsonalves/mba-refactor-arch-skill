'use strict';

class EnrollmentRepository {
  constructor(db) {
    this.db = db;
  }

  create(userId, courseId) {
    const info = this.db
      .prepare('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)')
      .run(userId, courseId);
    return info.lastInsertRowid;
  }
}

module.exports = EnrollmentRepository;
