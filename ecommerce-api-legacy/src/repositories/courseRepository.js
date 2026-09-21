'use strict';

class CourseRepository {
  constructor(db) {
    this.db = db;
  }

  findActiveById(id) {
    return this.db
      .prepare('SELECT * FROM courses WHERE id = ? AND active = 1')
      .get(id);
  }

  findAll() {
    return this.db.prepare('SELECT * FROM courses').all();
  }
}

module.exports = CourseRepository;
