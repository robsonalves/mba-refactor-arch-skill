'use strict';

const HttpError = require('../errors/httpError');

// Deletes a user preserving referential integrity (cascade in one transaction).
class UserService {
  constructor({ db, userRepository }) {
    this.db = db;
    this.users = userRepository;
  }

  deleteUser(id) {
    const run = this.db.transaction(() => {
      // ON DELETE CASCADE removes enrollments/payments; no orphan rows left.
      const info = this.users.deleteById(id);
      if (info.changes === 0) throw new HttpError(404, 'Usuário não encontrado');
    });
    run();
    return { msg: 'Usuário deletado' };
  }
}

module.exports = UserService;
