'use strict';

const bcrypt = require('bcrypt');
const HttpError = require('../errors/httpError');
const { PaymentStatus } = require('../constants');

// Business rule of checkout, isolated from HTTP. Runs inside a DB transaction.
class CheckoutService {
  constructor({
    db,
    userRepository,
    courseRepository,
    enrollmentRepository,
    paymentRepository,
    auditLogRepository,
    paymentGateway,
    bcryptRounds,
  }) {
    this.db = db;
    this.users = userRepository;
    this.courses = courseRepository;
    this.enrollments = enrollmentRepository;
    this.payments = paymentRepository;
    this.auditLogs = auditLogRepository;
    this.paymentGateway = paymentGateway;
    this.bcryptRounds = bcryptRounds;
  }

  checkout({ name, email, password, courseId, card }) {
    const course = this.courses.findActiveById(courseId);
    if (!course) throw new HttpError(404, 'Curso não encontrado');

    // Payment authorization decided before touching the DB.
    const status = this.paymentGateway.charge(card);
    if (status === PaymentStatus.DENIED) {
      throw new HttpError(400, 'Pagamento recusado');
    }

    const run = this.db.transaction(() => {
      let user = this.users.findByEmail(email);
      let userId;
      if (!user) {
        const passwordHash = bcrypt.hashSync(password, this.bcryptRounds);
        userId = this.users.create(name, email, passwordHash);
      } else {
        userId = user.id;
      }

      const enrollmentId = this.enrollments.create(userId, courseId);
      this.payments.create(enrollmentId, course.price, status);
      this.auditLogs.record(`Checkout curso ${courseId} por ${userId}`);
      return enrollmentId;
    });

    const enrollmentId = run();
    return { msg: 'Sucesso', enrollment_id: enrollmentId };
  }
}

module.exports = CheckoutService;
