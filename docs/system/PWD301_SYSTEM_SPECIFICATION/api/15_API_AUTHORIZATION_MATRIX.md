# API Authorization Matrix

| Endpoint group | Student | Instructor | Admin | Object check |
|---|---|---|---|---|
| Auth self-service | Self | Self | Self | token/User owner |
| Course catalog | Published | Published + own drafts | All | lifecycle visibility |
| Course/Lesson writes | — | Current owner | Override with policy | course owner/current manager |
| Enrollment/Attempt writes | Self | Self-as-Student | Self-as-Student | authenticated Student owns enrollment/attempt |
| Question/Assessment writes | — | Current Course | Override with reason | resource→Course |
| Grade | — | Current Course | Override/reason | Attempt→Assessment→Course |
| Files | Authorized learner read | Current Course manage | Policy | logical reference/resource |
| Import/AI generation | — | Current Course | Policy | source and Course authorization |
| AI chat | Own authorized scope | role/context scope | role/context scope | prefilter every source |
| Notifications | Own | Own | Own | recipient ID |
| Admin ops | — | — | Required | reauth/reason/confirmation as action requires |
