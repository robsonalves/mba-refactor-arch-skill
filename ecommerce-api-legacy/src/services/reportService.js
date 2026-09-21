'use strict';

const { PaymentStatus } = require('../constants');

// Aggregates the single JOIN result into the legacy report shape.
class ReportService {
  constructor({ reportRepository }) {
    this.reportRepository = reportRepository;
  }

  financialReport() {
    const rows = this.reportRepository.financialRows();
    const byCourse = new Map();

    for (const row of rows) {
      if (!byCourse.has(row.course_id)) {
        byCourse.set(row.course_id, {
          course: row.course_title,
          revenue: 0,
          students: [],
        });
      }

      // LEFT JOIN yields a row with null student when a course has no enrollment.
      if (row.student_name === null && row.payment_amount === null) continue;

      const courseData = byCourse.get(row.course_id);
      if (row.payment_status === PaymentStatus.PAID) {
        courseData.revenue += row.payment_amount;
      }
      courseData.students.push({
        student: row.student_name || 'Unknown',
        paid: row.payment_amount != null ? row.payment_amount : 0,
      });
    }

    return Array.from(byCourse.values());
  }
}

module.exports = ReportService;
