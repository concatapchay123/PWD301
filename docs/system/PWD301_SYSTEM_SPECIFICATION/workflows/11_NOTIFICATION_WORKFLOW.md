# Notification Workflow

Business transaction persists `notification_events`/in-app notification/outbox intent as appropriate → commit primary action → worker fan-out/email delivery → unique dedupe prevents duplicate recipient/channel → transient email failure retries → terminal failure logged/alerted without rolling back business action. User preferences apply only to optional categories.
