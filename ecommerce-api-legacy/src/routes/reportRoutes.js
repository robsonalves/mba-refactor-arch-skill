'use strict';

const { Router } = require('express');

function reportRoutes(reportController) {
  const router = Router();
  router.get('/admin/financial-report', reportController.financialReport);
  return router;
}

module.exports = reportRoutes;
