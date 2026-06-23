import pytest

from src.database.models import Branch, User
from src.utils.exceptions import AuthenticationError, NotFoundError, ValidationError
from src.utils.helpers import hash_password, verify_password


@pytest.fixture(autouse=True)
def _fix_repository_imports():
    import src.repositories as repos

    missing = {}

    if not hasattr(repos, "BranchRepository"):

        class _BranchRepo:
            def get_by_code(self, session, code):
                return session.query(Branch).filter_by(code=code).first()

        repos.BranchRepository = _BranchRepo
        missing["BranchRepository"] = _BranchRepo

    if not hasattr(repos, "AuditLogRepository"):
        from src.repositories.sync_repository import AuditLogRepository as _AuditLogRepo

        repos.AuditLogRepository = _AuditLogRepo
        missing["AuditLogRepository"] = _AuditLogRepo

    from src.repositories.sync_repository import AuditLogRepository as OrigAuditLogRepo
    from src.repositories.user_repository import UserRepository as OrigUserRepo

    if not hasattr(repos, "UserRepository"):
        repos.UserRepository = OrigUserRepo

    # --- Patches ---
    import sqlalchemy as sa
    from src.database.models import AuditLog

    class PatchedAuditLogRepo(OrigAuditLogRepo):
        def create(self, session, **kwargs):
            max_id = session.query(sa.func.max(AuditLog.id)).scalar() or 0
            kwargs.setdefault("id", max_id + 1)
            return super().create(session, **kwargs)

    repos.AuditLogRepository = PatchedAuditLogRepo

    orig_get_by_username = OrigUserRepo.get_by_username

    def _patched_get_by_username(self, username, session=None):
        return orig_get_by_username(self, username, session=session)

    OrigUserRepo.get_by_username = _patched_get_by_username

    yield

    OrigUserRepo.get_by_username = orig_get_by_username
    repos.AuditLogRepository = OrigAuditLogRepo

    for name, cls in missing.items():
        delattr(repos, name)


@pytest.fixture(scope="function", autouse=True)
def _reset_auth_service():
    from src.services.auth_service import AuthService

    AuthService._instance = None
    AuthService._initialized = False


class TestLogin:
    def test_login_success(self, db_session, sample_user, sample_branch):
        from src.services.auth_service import AuthService

        auth = AuthService()
        result = auth.login("testuser", "Pass123", "MB001")

        assert result is not None
        assert result["username"] == "testuser"
        assert result["full_name"] == "Test User"
        assert result["branch_code"] == "MB001"
        assert result["branch_name"] == "Main Branch"

    def test_login_failure_wrong_password(self, db_session, sample_user, sample_branch):
        from src.services.auth_service import AuthService

        auth = AuthService()
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            auth.login("testuser", "WrongPass99", "MB001")

    def test_login_failure_wrong_username(self, db_session, sample_branch):
        from src.services.auth_service import AuthService

        auth = AuthService()
        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            auth.login("nonexistent", "Pass123", "MB001")

    def test_login_wrong_branch_code(self, db_session, sample_user):
        from src.services.auth_service import AuthService

        auth = AuthService()
        with pytest.raises(NotFoundError, match="Branch with code"):
            auth.login("testuser", "Pass123", "WRONG")

    def test_login_wrong_branch_assignment(
        self, db_session, sample_branch, sample_role
    ):
        from src.services.auth_service import AuthService

        other_branch = Branch(
            name="Other Branch", code="OTH01", is_active=1
        )
        db_session.add(other_branch)
        db_session.flush()

        user = User(
            username="assigned_user",
            password_hash=hash_password("Pass123"),
            full_name="Assigned User",
            branch_id=other_branch.id,
            role_id=sample_role.id,
            is_active=1,
        )
        db_session.add(user)
        db_session.flush()

        auth = AuthService()
        with pytest.raises(AuthenticationError, match="not assigned"):
            auth.login("assigned_user", "Pass123", "MB001")

    def test_login_inactive_user(self, db_session, sample_role, sample_branch):
        from src.services.auth_service import AuthService

        inactive = User(
            username="inactive_user",
            password_hash=hash_password("Pass123"),
            full_name="Inactive",
            role_id=sample_role.id,
            branch_id=sample_branch.id,
            is_active=0,
        )
        db_session.add(inactive)
        db_session.flush()

        auth = AuthService()
        with pytest.raises(AuthenticationError, match="deactivated"):
            auth.login("inactive_user", "Pass123", "MB001")

    def test_login_inactive_branch(
        self, db_session, sample_role, sample_user, sample_branch
    ):
        from src.services.auth_service import AuthService

        sample_branch.is_active = 0
        db_session.commit()

        auth = AuthService()
        with pytest.raises(AuthenticationError, match="inactive"):
            auth.login("testuser", "Pass123", "MB001")


class TestChangePassword:
    def test_change_password_success(self, db_session, sample_user):
        from src.services.auth_service import AuthService

        auth = AuthService()
        auth.change_password(sample_user.id, "Pass123", "NewPass456")

        db_session.expire_all()
        user = db_session.query(User).filter_by(id=sample_user.id).first()
        assert verify_password("NewPass456", user.password_hash) is True

    def test_change_password_wrong_old(self, db_session, sample_user):
        from src.services.auth_service import AuthService

        auth = AuthService()
        with pytest.raises(ValidationError, match="Current password is incorrect"):
            auth.change_password(sample_user.id, "WrongOld", "NewPass456")

    def test_change_password_invalid_new(self, db_session, sample_user):
        from src.services.auth_service import AuthService

        auth = AuthService()
        with pytest.raises(ValidationError):
            auth.change_password(sample_user.id, "Pass123", "short")

    def test_change_password_user_not_found(self, db_session):
        from src.services.auth_service import AuthService

        auth = AuthService()
        with pytest.raises(NotFoundError):
            auth.change_password(99999, "Pass123", "NewPass456")

    def test_login_updates_last_login(self, db_session, sample_user, sample_branch):
        from sqlalchemy import select

        from src.database.models import User
        from src.services.auth_service import AuthService

        assert sample_user.last_login is None

        auth = AuthService()
        auth.login("testuser", "Pass123", "MB001")

        last_login = db_session.execute(
            select(User.last_login).where(User.id == sample_user.id)
        ).scalar()
        assert last_login is not None


class TestSingleton:
    def test_auth_service_is_singleton(self):
        from src.services.auth_service import AuthService

        a1 = AuthService()
        a2 = AuthService()
        assert a1 is a2
