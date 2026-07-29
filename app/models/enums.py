import enum

class UserType(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    SYSTEM = "system"
    
class ProfileStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"
    disabled = "disabled"
    
class CardStatus(str, enum.Enum):
    inactive = "inactive"
    active = "active"
    deactivated = "deactivated"
    lost = "lost"
    disabled = "disabled"
    
class FeedbackType(enum.Enum):
    bug = "bug"
    suggestion = "suggestion"
    other = "other"
    
class FeedbackStatus(enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"