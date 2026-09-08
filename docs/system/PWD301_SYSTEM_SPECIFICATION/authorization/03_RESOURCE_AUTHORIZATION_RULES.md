# Resource Authorization Rules

Every service starts from the authenticated actor and loads the requested resource by opaque public ID. It then checks status and relationship: current Course owner/manager, active enrollment, Attempt owner, Notification recipient, File reference visibility, or Admin override. Never authorize from a client-supplied course_id/user_id without joining/validating the actual resource. Previous ownership does not grant current Student detail access. Soft-deleted/archived state is part of authorization.
