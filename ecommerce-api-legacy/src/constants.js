'use strict';

// Domain constants — no magic strings/numbers scattered across the code.
const PaymentStatus = Object.freeze({
  PAID: 'PAID',
  DENIED: 'DENIED',
});

// Cards whose number starts with this prefix are approved by the test gateway.
const APPROVED_CARD_PREFIX = '4';

const DEFAULT_COURSE_ID = null;

module.exports = { PaymentStatus, APPROVED_CARD_PREFIX, DEFAULT_COURSE_ID };
