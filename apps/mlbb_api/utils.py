import os
from django.core.exceptions import ImproperlyConfigured


class BasePathProvider:
    """
    Provides base path from environment variable.
    This removes hard-locked encryption dependency.
    """

    ENV_KEY = "BASE_PATH"

    @classmethod
    def get_base_path(cls) -> str:
        base_path = os.getenv(cls.ENV_KEY)

        if not base_path:
            raise ImproperlyConfigured(
                f"{cls.ENV_KEY} environment variable is not set"
            )

        return base_path
