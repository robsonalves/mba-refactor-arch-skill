"""Envio de notificações por e-mail. Credenciais vêm da config (env)."""
import logging
import smtplib

from flask import current_app

from utils.helpers import now_utc

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.notifications = []

    def _config(self):
        cfg = current_app.config
        return cfg['SMTP_HOST'], cfg['SMTP_PORT'], cfg['SMTP_USER'], cfg['SMTP_PASSWORD']

    def send_email(self, to, subject, body):
        host, port, user, password = self._config()
        if not user or not password:
            logger.warning('SMTP não configurado; e-mail para %s não enviado', to)
            return False
        try:
            server = smtplib.SMTP(host, port)
            server.starttls()
            server.login(user, password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(user, to, message)
            server.quit()
            logger.info('Email enviado para %s', to)
            return True
        except Exception as exc:
            logger.error('Erro ao enviar email para %s: %s', to, exc)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': now_utc(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]


# Instância única compartilhada pelos services (ligada em TaskService).
notification_service = NotificationService()
