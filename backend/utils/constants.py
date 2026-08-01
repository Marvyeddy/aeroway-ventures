# TOPICS


class KafkaTopics:
    EMAIL_EVENTS = "email-events"
    NOTIFICATION_EVENTS = "notification-events"
    USER_EVENTS = "user-events"


# EVENT_TYPES
class KafkaEvents:
    EMAIL_SEND = "email.send"
    NOTIFICATION_CREATE = "notification.create"
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_UNREAD_COUNT = "notification.unread_count"
    USER_REGISTERED = "user.registered"
