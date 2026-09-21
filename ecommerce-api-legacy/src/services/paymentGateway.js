'use strict';

const { PaymentStatus, APPROVED_CARD_PREFIX } = require('../constants');

// Injected payment gateway. Never logs the PAN nor the gateway key.
class PaymentGateway {
  constructor(apiKey) {
    this.apiKey = apiKey;
  }

  charge(card) {
    const approved = String(card).startsWith(APPROVED_CARD_PREFIX);
    return approved ? PaymentStatus.PAID : PaymentStatus.DENIED;
  }
}

module.exports = PaymentGateway;
