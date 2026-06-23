import logging
from datetime import datetime

from src.database.connection import db_manager
from src.database.models import AuditLog, Permission, User
from src.utils.exceptions import AuthenticationError, AuthorizationError, NotFoundError, ValidationError
from src.utils.helpers import hash_password, verify_password
from src.utils.validators import validate_password, validate_required
from src.repositories import AuditLogRepository, BranchRepository, UserRepository

logger = logging.getLogger(__name__)

ACTION_MAP = {
    "create": Permission.can_create,
    "read": Permission.can_read,
    "update": Permission.can_update,
    "delete": Permission.can_delete,
}


class AuthService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if AuthService._initialized:
            return
        AuthService._initialized = True
        self.user_repo = UserRepository()
        self.branch_repo = BranchRepository()
        self.audit_repo = AuditLogRepository()
        self._current_user = None
        self._current_branch = None

    @property
    def current_user(self):
        return self._current_user

    @property
    def current_branch(self):
        return self._current_branch

    def login(self, username, password, branch_code):
        validate_required(username, "Username")
        validate_required(password, "Password")
        validate_required(branch_code, "Branch code")

        with db_manager.get_session() as session:
            user = self.user_repo.get_by_username(username, session=session)
            if not user:
                raise AuthenticationError("Invalid username or password.")
            if not user.is_active:
                raise AuthenticationError("Account is deactivated. Contact administrator.")

            if not verify_password(password, user.password_hash):
                raise AuthenticationError("Invalid username or password.")

            branch = self.branch_repo.get_by_code(branch_code, session=session)
            if not branch:
                raise NotFoundError(f"Branch with code '{branch_code}' not found.")
            if not branch.is_active:
                raise AuthenticationError("Branch is inactive.")

            if user.branch_id is not None and user.branch_id != branch.id:
                raise AuthenticationError(
                    f"User '{username}' is not assigned to branch '{branch_code}'."
                )

            user.last_login = datetime.now()
            session.flush()

            self._current_user = user
            self._current_branch = branch

            self.audit_repo.create(
                session=session,
                user_id=user.id,
                branch_id=branch.id,
                action="LOGIN",
                resource="auth",
                details=f"User '{username}' logged in to branch '{branch_code}'",
            )

            role_name = user.role.name if user.role else None

            return {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role_id": user.role_id,
                "role_name": role_name,
                "branch_id": branch.id,
                "branch_name": branch.name,
                "branch_code": branch.code,
            }

    def logout(self):
        if not self._current_user:
            return

        with db_manager.get_session() as session:
            self.audit_repo.create(
                session=session,
                user_id=self._current_user.id,
                branch_id=self._current_branch.id if self._current_branch else None,
                action="LOGOUT",
                resource="auth",
                details=f"User '{self._current_user.username}' logged out",
            )

        self._current_user = None
        self._current_branch = None

    def change_password(self, user_id, old_password, new_password):
        validate_required(old_password, "Current password")
        validate_password(new_password)

        with db_manager.get_session() as session:
            user = self.user_repo.get_by_id(user_id, session=session)
            if not user:
                raise NotFoundError("User not found.")

            if not verify_password(old_password, user.password_hash):
                raise ValidationError("Current password is incorrect.")

            user.password_hash = hash_password(new_password)
            session.flush()

            self.audit_repo.create(
                session=session,
                user_id=user.id,
                branch_id=user.branch_id,
                action="CHANGE_PASSWORD",
                resource="users",
                resource_id=user.id,
                details=f"User '{user.username}' changed their password",
            )

    def create_user(self, admin_user, username, password, role_id, branch_id, full_name):
        validate_required(username, "Username")
        validate_password(password)
        validate_required(full_name, "Full name")

        with db_manager.get_session() as session:
            existing = self.user_repo.get_by_username(username, session=session)
            if existing:
                raise ValidationError(f"Username '{username}' is already taken.")

            user = self.user_repo.create(
                session=session,
                username=username,
                password_hash=hash_password(password),
                role_id=role_id,
                branch_id=branch_id,
                full_name=full_name,
                email=None,
                phone=None,
                is_active=1,
            )

            self.audit_repo.create(
                session=session,
                user_id=admin_user.id if hasattr(admin_user, "id") else admin_user,
                branch_id=admin_user.branch_id if hasattr(admin_user, "branch_id") else None,
                action="CREATE_USER",
                resource="users",
                resource_id=user.id,
                details=f"Created user '{username}' with role_id={role_id}",
            )

            return {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role_id": user.role_id,
                "branch_id": user.branch_id,
                "is_active": user.is_active,
            }

    def reset_password(self, admin_user, user_id, new_password):
        validate_password(new_password)

        with db_manager.get_session() as session:
            user = self.user_repo.get_by_id(user_id, session=session)
            if not user:
                raise NotFoundError("User not found.")

            user.password_hash = hash_password(new_password)
            session.flush()

            self.audit_repo.create(
                session=session,
                user_id=admin_user.id if hasattr(admin_user, "id") else admin_user,
                branch_id=admin_user.branch_id if hasattr(admin_user, "branch_id") else None,
                action="RESET_PASSWORD",
                resource="users",
                resource_id=user.id,
                details=f"Password reset for user '{user.username}'",
            )

    def get_users(self, branch_id=None):
        with db_manager.get_session() as session:
            users = self.user_repo.find(session=session, branch_id=branch_id)
            return [
                {
                    "id": u.id,
                    "username": u.username,
                    "full_name": u.full_name,
                    "email": u.email,
                    "phone": u.phone,
                    "role_id": u.role_id,
                    "role_name": u.role.name if u.role else None,
                    "branch_id": u.branch_id,
                    "branch_name": u.branch.name if u.branch else None,
                    "is_active": u.is_active,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                    "created_at": u.created_at.isoformat() if hasattr(u, "created_at") and u.created_at else None,
                }
                for u in users
            ]

    def has_permission(self, resource, action):
        if not self._current_user:
            return False

        action_col = ACTION_MAP.get(action)
        if action_col is None:
            return False

        with db_manager.get_session() as session:
            perm = (
                session.query(Permission)
                .filter(
                    Permission.role_id == self._current_user.role_id,
                    Permission.resource == resource,
                )
                .first()
            )
            if not perm:
                return False
            return bool(getattr(perm, action_col.name))

    def require_permission(self, resource, action):
        if not self.has_permission(resource, action):
            username = self._current_user.username if self._current_user else "Unknown"
            raise AuthorizationError(
                f"User '{username}' lacks '{action}' permission on '{resource}'."
            )
