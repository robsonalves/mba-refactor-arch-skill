'use strict';

const { Router } = require('express');
const { checkoutRules } = require('../middlewares/validate');

// Only route registration — no SQL, no business rule.
function checkoutRoutes(checkoutController) {
  const router = Router();
  router.post('/checkout', checkoutRules, checkoutController.create);
  return router;
}

module.exports = checkoutRoutes;
