from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.hashers import check_password, make_password

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username=username, email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # Address
    address = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)

    role = models.ForeignKey(
        "roles.Role",
        verbose_name="user_role",
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(null=True, blank=True)

    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True, null=True)
    is_staff = models.BooleanField(default=False, null=True)

    date_joined = models.DateTimeField(auto_now_add=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username",]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username

    # ============================
    # COMPUTED / UI-FRIENDLY FIELDS
    # ============================

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def status(self):
        return "Active" if self.is_active else "Inactive"

    @property
    def profile_picture_url(self):
        return self.profile_picture.url if self.profile_picture else None

    # ----------------------------
    # HELPERS
    # ----------------------------

    def _split_to_list(self, value):
        """
        Converts comma-separated strings into lists
        """
        if not value:
            return []
        return [v.strip() for v in value.split(",")]

    # ----------------------------
    # SAFE ACTIONS
    # ----------------------------

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def activate(self):
        self.is_active = True
        self.save(update_fields=["is_active"])


class PasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password = models.CharField(max_length=128)  # Store hashed password
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Password Histories"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Hash the password before saving
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    