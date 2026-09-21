'use strict';

const express = require('express');
const cors = require('cors');

const config = require('./config');
const { createDatabase } = require('./db/database');

const UserRepository = require('./repositories/userRepository');
const CourseRepository = require('./repositories/courseRepository');
const EnrollmentRepository = require('./repositories/enrollmentRepository');
const PaymentRepository = require('./repositories/paymentRepository');
const AuditLogRepository = require('./repositories/auditLogRepository');
const ReportRepository = require('./repositories/reportRepository');

const PaymentGateway = require('./services/paymentGateway');
const CheckoutService = require('./services/checkoutService');
const ReportService = require('./services/reportService');
const UserService = require('./services/userService');

const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');

const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const { errorHandler, notFound } = require('./middlewares/errorHandler');

// Composition root: the only place that wires every dependency together (DI).
function buildApp(db) {
  const userRepository = new UserRepository(db);
  const courseRepository = new CourseRepository(db);
  const enrollmentRepository = new EnrollmentRepository(db);
  const paymentRepository = new PaymentRepository(db);
  const auditLogRepository = new AuditLogRepository(db);
  const reportRepository = new ReportRepository(db);

  const paymentGateway = new PaymentGateway(config.paymentGatewayKey);

  const checkoutService = new CheckoutService({
    db,
    userRepository,
    courseRepository,
    enrollmentRepository,
    paymentRepository,
    auditLogRepository,
    paymentGateway,
    bcryptRounds: config.bcryptRounds,
  });
  const reportService = new ReportService({ reportRepository });
  const userService = new UserService({ db, userRepository });

  const checkoutController = new CheckoutController({ checkoutService });
  const reportController = new ReportController({ reportService });
  const userController = new UserController({ userService });

  const app = express();
  app.use(
    cors(
      config.corsOrigins.length > 0 ? { origin: config.corsOrigins } : { origin: false }
    )
  );
  app.use(express.json({ limit: config.jsonBodyLimit }));

  app.use('/api', checkoutRoutes(checkoutController));
  app.use('/api', reportRoutes(reportController));
  app.use('/api', userRoutes(userController));

  app.use(notFound);
  app.use(errorHandler);

  return app;
}

function start() {
  const db = createDatabase(config.dbPath);
  const app = buildApp(db);
  app.listen(config.port, () => {
    console.log(`LMS API rodando na porta ${config.port}...`);
  });
}

if (require.main === module) {
  start();
}

module.exports = { buildApp, start };
