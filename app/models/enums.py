import enum


class DeliveryType(str, enum.Enum):
    HOME = "HOME"
    OFFICE = "OFFICE"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    SHIPPING = "SHIPPING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class AdminRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    STAFF = "staff"


class Season(str, enum.Enum):
    SUMMER = "SUMMER"
    WINTER = "WINTER"
    SPRING = "SPRING"
    AUTUMN = "AUTUMN"
    ALL_SEASON = "ALL_SEASON"
